#!/usr/bin/env python3
"""Editorial consistency pass for the current 286 department activity articles.

Update original static HTML and matching archive metadata. Never synthesize facts
about people, prize amounts, placements, attendance, or technologies. The
additional educational paragraphs explain *verified terms mentioned in source*
rather than claiming unrecorded activities. Preserve every URL, image and date.
"""
from __future__ import annotations
from collections import Counter
from datetime import date
from pathlib import Path
import html
import json
import re
from bs4 import BeautifulSoup
from activity_promo import CURATED

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "activities" / "index.html"
REPORT = ROOT / "reports" / "activity_editorial_consistency_2026-10-25.md"
JSON_REPORT = ROOT / "data" / "activity_editorial_consistency_2026-10-25.json"
CARD = re.compile(r'<article class="activity-card">.*?</article>', re.S)
SCHEMA = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
BODY = re.compile(r'(<div class="activity-content">)(.*?)(<div class="activity-cta">)', re.S)
DISALLOWED = re.compile(r'[·•・—–―“”‘’「」『』【】\[\]!?★☆✅✓📌🎉]')
SPLIT = re.compile(r'(?<=[.!?。])\s+(?=[가-힣A-Za-z0-9「“(])')
STOP_PHRASES = (
    "많은 관심과 응원 부탁드립니다!",
    "앞으로도 많은 관심과 응원 부탁드립니다!",
    "이번 행사에 많은 관심과 참여 부탁드립니다.",
    "열심히 하는 모습이 참 보기 좋습니다.",
    "진심으로 큰 박수와 축하를 보냅니다.",
)

OVERRIDES = {
    "kopo-443890": "교남 소망의 집에서 컴퓨터 유지보수와 지역사회 봉사활동",
    "kopo-591393": "2020 한이음 ICT 공모전 참가 동아리 소개 카드뉴스",
    "kopo-527126": "2019 ICNCT 국제학술대회에서 학과 교수진 연구논문 발표",
    "kopo-738804": "ACK 2024 논문경진대회 동상 수상, 맵리듀스 데이터 압축 연구",
    "kopo-738801": "ACK 2024 논문경진대회 동상 수상, 학생과 교수 공동 연구",
    "sesac-hackathon-grand-prize-2025": "2025 서울시 새싹 해커톤 대상 수상, AI 서비스 구현 성과",
    "alumni-ha-jae-hyeong-lecture-2026": "부산대 대학원 진학 졸업생 초청, 학업과 진로 경험 공유",
    "department-funding-2025": "AI와 클라우드 교육환경 고도화, 학과 개편 사업 10억 원 확보",
    "department-reorganization-2025": "빅데이터소프트웨어공학과 개편, AI와 클라우드 실습 강화",
    "kopo-777680": "효성ITX 이주현 팀장 특강, 기업이 원하는 IT 인재와 직무 역량",
    "kopo-773576": "엔씨IDS 재직 졸업생 초청, 개발자 취업 준비와 성장 경험",
    "kopo-770067": "졸업생이 전하는 AI 에이전트 구현, LangChain과 LangGraph 특강",
    "kopo-770073": "에이전시프로 기술지도, Python과 OpenCV 영상처리 활용",
    "kopo-750066": "2학년 선배 주도 멘토링, Rocky Linux와 MariaDB 개발환경 구축",
    "kopo-750981": "선후배 개발 멘토링, Spring Boot와 MariaDB 연동 실습",
    "kopo-765955": "EBS와 강서양천교육지원청 학습전략설명회 진로 특강 참여",
    "kopo-445198": "2016 김영운 교수의 빅데이터 분석 활용과 R 프로그래밍 기고",
    "kopo-450315": "2017 강서구 SNS 톡톡 기자단 모집 안내, 종료된 기록",
    "kopo-460887": "2017 창업아이템 경진대회 참가 모집 안내, 종료된 기록",
    "kopo-727467": "카카오엔터테인먼트 개발자 초청, Spring Framework 실무 특강",
    "kopo-762210": "2025 프로젝트경진대회 우수상과 장려상, AI와 클라우드 작품",
    "teacher-generative-ai-r-training-2026": "고교 교사 대상 생성형 AI와 R 데이터 분석 실습 연수",
    "teacher-ai-llm-workshop-2026": "고교 교사 대상 Python과 LLM 기반 인공지능 실습 연수",
    "public-vibe-coding-class-2026": "일반인 대상 생성형 AI 활용 Python 바이브코딩 실습 교육",
    "dongmyeong-school-vibe-coding-2026": "동명중학교 학생 대상 AI 바이브코딩 게임 개발 진로체험",
    "social-data-career-trends": "소셜데이터 분석으로 알아보는 미래 직업과 관심 트렌드 체험",
    "gangseo-job-fair-2026": "2026 강서구 취업박람회 참여, 2학년 학생들의 IT 직무 탐색",
    "kopo-454182": "학과 실습실 이전, 제3교육관에서 본관 3층으로",
    "kopo-459546": "1학년과 2학년 교류를 위한 학과 소그룹 모임과 다과회",
    "kopo-454696": "숭실대학교 송관호 교수의 인문학과 ICT 서적 기증",
    "kopo-765578": "2025 서울시 새싹 해커톤 본선 진출, 학생팀의 AI 서비스 기획",
    "kopo-763327": "ACK 2025 논문경진대회 동상, 비전언어모델 기반 얼굴 초해상도 연구",
    "kopo-746968": "선후배 Java 멘토링, 반복문 작성과 제어 흐름 실습",
    "kopo-745970": "경력단절여성 취업 지원, 방과후 컴퓨터와 코딩지도사 과정 개강",
    "kopo-734728": "코웨이 재직 졸업생 황윤영, SW 개발 업무와 취업 준비 특강",
    "kopo-734725": "인문학과 빅데이터 융합, 데이터 기술의 활용 범위 특강",
    "kopo-727475": "퀴즈톡 앱 UI/UX 개선 프로젝트, 미래내일 일경험 사업 설명회",
    "kopo-727472": "Spring AI 실무 특강, LLM과 RAG를 활용한 AI 애플리케이션 개발",
    "kopo-727468": "방과후 컴퓨터와 코딩지도사 교육과정 수료식, 여성 재취업 지원",
    "kopo-707049": "빅데이터 분석 전문가 진로체험 2기, 실습 중심 프로그램 운영",
    "kopo-707048": "카카오엔터테인먼트 손성용 개발자, 객체지향 설계와 JPA 특강",
    "kopo-707041": "LF융합실습지원센터 졸업작품 발표회, 학생 프로젝트 성과 공유",
    "kopo-699022": "강서양천교육지원청 협력, 고교 교원 빅데이터 실습 직무연수",
    "kopo-699015": "큐버스랩 전창섭 대표 초청, 빅데이터와 AI 서비스 실무 특강",
    "kopo-663560": "여름방학 5일간 Spring Boot 기반 웹 애플리케이션 개발 특강",
    "kopo-658306": "강서양천교육지원청 중등학교장 대상 빅데이터 활용 연수",
    "kopo-658296": "제19회 임베디드 SW 경진대회, GAS GAS GAS팀 회장상 수상",
    "kopo-633734": "2021 춘계종합학술발표회 우수논문상, 학과 학생 공동 연구",
    "kopo-621351": "블록체인 기술과 미래 전망, 한국블록체인스타트업협회 전문가 특강",
    "kopo-621350": "엑셈 재직 졸업생 박창원 초청, 빅데이터 개발자 취업 특강",
    "kopo-602150": "제4회 벤처창업아이템 경진대회 동상, 슈퍼개발자팀 수상",
    "kopo-614467": "2020 한이음 ICT 공모전 동상 수상, 슈퍼개발자 동아리",
    "kopo-614469": "2020 한이음 ICT 공모전 입상, 거북목 동아리 프로젝트",
    "kopo-602148": "2020 졸업작품경진대회 수상, 4기 재학생 프로젝트 성과",
    "kopo-591398": "여름방학 5일간 Spring Framework 실습, MVC와 게시판 구현",
    "kopo-591394": "1학년과 2학년이 함께한 멘토 멘티 데이, 학기말 교류 행사",
    "kopo-591392": "2020 한이음 ICT 공모전, 학과 학생 3개 팀 도전",
    "kopo-583306": "시스원 재직 1기 졸업생 김상훈, 실무 경험과 진로 특강",
    "kopo-558040": "2019 SW인재페스티벌 참가, 소프트웨어 작품 시연과 전시 관람",
    "kopo-516833": "졸업생 홈커밍데이, 시스원과 씨엘정보 선배들의 개발 실무 공유",
    "kopo-516832": "YTN 방송국 현장 견학, 뉴스 제작과 정보시스템 기술 학습",
    "kopo-499817": "경찰청 문구백 부장 특강, 정보시스템 이해와 IT 취업 진로",
    "kopo-498290": "TNMS 최태병 본부장 특강, TV 시청률 조사 기술과 데이터 분석",
    "kopo-497019": "KCC정보통신 변재영 연구원 특강, 금융권 블록체인 적용 사례",
    "kopo-467181": "학과 창업아이템 경진대회 시상식, 학생 창업 도전 성과",
    "kopo-464839": "제1회 창업아이템 경진대회 참가, 학생들의 아이디어 발표",
    "kopo-464124": "윤효근 박사 초청, 빅데이터 기술과 산업 적용 사례 특강",
    "kopo-463924": "현직자 멘토 초청 특강과 선후배 교류, 학과 멘토의 날",
    "kopo-463762": "우장산 봄맞이 산책, 학과 학생들의 친목과 교류 활동",
    "kopo-445461": "교남 소망의 집 방문, 네 번째 지역사회 봉사활동과 시설 정리",
    "kopo-448025": "강서구청 감사장 수상, 학과의 지속적인 지역사회 봉사활동",
    "kopo-699013": "AI와 블록체인 기반 디지털 다이어리, 한이음 ICT 멘토링 사업 선정",
    "kt-researcher-career-lecture-2026": "KT 현직자 초청, 빅데이터와 소프트웨어 개발 직무 특강",
}
# Use one title separator: comma. Official technical product hyphens and ranges
# are preserved, because removing them would corrupt names such as K-PaaS.
def clean_title(original: str) -> str:
    v = html.unescape(original).strip()
    v = re.sub(r'[“”‘’"\'「」『』【】\[\]]', '', v)
    v = re.sub(r'\s*[·•・—–―:;|]\s*', ', ', v)
    v = re.sub(r'\s+-\s+', ', ', v)
    v = v.replace('…','')
    v = re.sub(r'\s*&\s*', ' 및 ', v)
    v = re.sub(r'[!?★☆✅✓📌🎉]', '', v)
    v = re.sub(r'\(\s*종료\s*\)', ', 종료된 기록', v)
    v = re.sub(r'\s*\(([^)]{1,22})\)', r' \1', v)
    v = re.sub(r'(?<=\s)/(?=\s)', '및', v)
    v = re.sub(r'\s*,\s*,+', ', ', v)
    v = re.sub(r'[,.\s]+$', '', v)
    v = re.sub(r'\s+', ' ', v).strip()
    if DISALLOWED.search(v):
        raise ValueError(f"Title still has inconsistent punctuation: {v}")
    return v

# Explain only named technologies that are literally present in the original
# article; factual technology background is explicitly separated from reports.
TECH = [
    ("GPU", "GPU는 많은 계산을 병렬로 처리하는 장치로, 인공지능 모델 학습과 대규모 데이터 연산에 사용됩니다."),
    ("클라우드", "클라우드는 필요에 따라 서버와 저장소 등 IT 자원을 제공하고 서비스를 배포하고 운영하도록 지원하는 컴퓨팅 방식입니다."),
 ("LangGraph", "LangGraph는 여러 단계의 AI 모델 호출과 상태 전이를 연결해 복잡한 에이전트 작업 흐름을 설계할 때 활용됩니다."),
 ("LangChain", "LangChain은 언어모델을 프롬프트와 데이터, 외부 도구에 연결해 응용 서비스를 구현할 때 사용하는 개발 프레임워크입니다."),
 ("K-PaaS", "K-PaaS는 애플리케이션 개발과 배포, 운영을 지원하는 개방형 클라우드 플랫폼 기술입니다."),
 ("Spring Boot", "Spring Boot는 자바 기반 서버 애플리케이션을 구성하고 웹 API와 데이터베이스 연동 기능을 구현하는 데 활용됩니다."),
 ("Apache Spark", "Apache Spark는 여러 컴퓨팅 자원을 활용해 대규모 데이터를 분산 처리하는 엔진입니다."),
 ("Hadoop", "Hadoop은 대규모 데이터를 여러 서버에 저장하고 분산 처리하기 위한 기술 생태계입니다."),
 ("OpenCV", "OpenCV는 영상·이미지 데이터를 읽고 변환하거나 시각적 특징을 분석할 때 사용하는 컴퓨터 비전 라이브러리입니다."),
 ("TensorFlow", "TensorFlow는 머신러닝과 딥러닝 모델을 설계하고 학습·추론할 때 활용하는 프레임워크입니다."),
 ("MyBatis", "MyBatis는 SQL을 명시적으로 작성하고 자바 애플리케이션과 데이터베이스 사이의 데이터 처리를 연결하는 프레임워크입니다."),
 ("MariaDB", "MariaDB는 SQL 기반으로 데이터를 저장하고 조회할 수 있는 관계형 데이터베이스 관리 시스템입니다."),
 ("MongoDB", "MongoDB는 문서 형태의 데이터를 저장하는 NoSQL 데이터베이스로, 유연한 데이터 구조를 다룰 때 활용됩니다."),
 ("Docker", "Docker는 애플리케이션과 실행에 필요한 환경을 컨테이너로 묶어 일관되게 실행하도록 지원합니다."),
 ("Kubernetes", "Kubernetes는 컨테이너 애플리케이션의 배포, 확장, 운영을 자동화하는 플랫폼입니다."),
 ("DevOps", "DevOps는 개발과 운영 과정을 연계하고 빌드·검증·배포 자동화 및 협업을 개선하는 접근 방식입니다."),
 ("SQL", "SQL은 관계형 데이터베이스에서 데이터를 조회·집계·변경하는 데 사용하는 표준 질의 언어입니다."),
 ("RStudio", "RStudio는 R 언어로 데이터 정제, 통계 분석 및 시각화 작업을 수행하도록 돕는 개발환경입니다."),
 ("Flutter", "Flutter는 하나의 코드 기반으로 여러 플랫폼의 사용자 인터페이스를 구현할 수 있는 개발 도구입니다."),
 ("Python", "Python은 데이터 분석·자동화·인공지능 모델 구현 등 다양한 개발 작업에 활용되는 프로그래밍 언어입니다."),
 ("Java", "Java는 객체지향 프로그래밍과 기업용 서버 애플리케이션 개발에 널리 활용되는 언어입니다."),
 ("LLM", "대규모 언어모델 LLM은 자연어 입력을 바탕으로 텍스트 생성과 분류, 요약 등 언어 처리 기능을 구현할 때 활용됩니다."),
 ("OCR", "OCR은 이미지나 스캔 문서에 포함된 글자를 추출해 디지털 텍스트로 변환하는 기술입니다."),
]
TOPIC_CONTEXT = {
 "수상·성과": "수상 결과와 함께 작품의 문제 정의, 적용 기술, 구현 방법을 살펴보면 공모전 경험이 소프트웨어 개발 역량과 어떻게 연결되는지 이해하는 데 도움이 됩니다.",
 "취업·진로": "IT 직무를 탐색할 때는 채용기업의 업무 분야와 요구 기술을 확인하고, 자신의 프로젝트 경험을 직무별 역량과 연결해 정리하는 과정이 중요합니다.",
 "멘토링·진로": "선후배의 학습·취업 경험을 비교할 때는 준비 과정에서 활용한 기술, 프로젝트 수행 방식, 진로 선택에 영향을 준 요소를 함께 확인할 수 있습니다.",
 "전문가 특강": "산업 현장 사례는 교과목에서 배우는 기술이 기업의 개발·운영 업무와 어떤 관계가 있는지 이해하는 참고 자료가 됩니다.",
 "진로체험": "단순한 기술 설명을 넘어 직접 데이터를 다루거나 프로그램을 구현하는 경험은 소프트웨어와 인공지능 분야의 진로를 구체적으로 탐색하는 데 도움이 됩니다.",
 "교원 연수": "교원 연수의 실습 도구와 학습 주제는 데이터를 분석하고 AI 기술을 수업에 적용하는 방법을 탐색하기 위한 참고 사례입니다.",
 "학생 프로젝트": "프로젝트에서는 구현 결과뿐 아니라 요구사항, 기능 설계, 사용 기술, 팀의 문제 해결 과정을 함께 살펴볼 때 학습 성과를 더 구체적으로 이해할 수 있습니다.",
 "연구·학술": "연구 활동을 이해할 때는 문제 정의와 데이터·실험 방법, 분석 결과를 구분해 살펴보는 것이 중요합니다.",
 "산학협력": "기업과 학교가 다루는 기술 과제를 통해 실제 개발 환경에서 필요한 문제 정의, 기술 검토, 성과 검증 과정을 살펴볼 수 있습니다.",
 "사회공헌·봉사": "지역사회 활동은 기술적 지식뿐 아니라 사용자와의 소통, 현장 문제 해결, 협업의 중요성을 살펴보는 기회입니다.",
 "지역사회 교육": "참가 대상에 맞춰 소프트웨어와 데이터 기술을 설명하고 실습하는 활동은 기술 활용의 범위를 넓히는 사례가 됩니다.",
 "학과 행사": "학과 행사는 학생들의 교류와 공동 활동을 기록한 자료로, 전공 수업 외의 캠퍼스 생활을 확인할 수 있습니다.",
}
FACT_CORRECTIONS = {
 "kopo-591393": (
  r'<section><h2>행사 내용</h2><p>.*?</p></section><section><h2>참여 활동</h2><p>.*?</p></section>',
  '<section><h2>2020 한이음 ICT 공모전 참가 동아리</h2><p>2020년 한국폴리텍대학 서울강서캠퍼스 학과 게시판에서 한이음 ICT 공모전에 참가하는 동아리 소개 카드뉴스 제작 소식을 알렸습니다. 당시 동아리의 공모전 참가 활동을 안내하기 위한 자료입니다.</p></section>'
 ),
 "department-reorganization-2025": (
  r'2025년 발표에서는 2026학년도 신입생부터 빅데이터소프트웨어공학과를 빅데이터소프트웨어공학과로 개편한다고 설명했습니다. 현재 학과 공식 명칭은 빅데이터소프트웨어공학과입니다.',
  '2025년 발표된 학과 개편은 2026학년도 신입생부터 인공지능과 소프트웨어 개발, 클라우드 실습 중심의 교육을 강화하는 방향을 담고 있습니다. 현재 공식 학과 명칭은 빅데이터소프트웨어공학과입니다.'
 ),
}

def plaintext(fragment: str) -> str:
    return " ".join(BeautifulSoup(fragment, "html.parser").stripped_strings)

def meaningful_sentences(text: str) -> list[str]:
    v = " ".join(text.split())
    sentences = [s.strip() for s in SPLIT.split(v)]
    return [s for s in sentences if len(s)>16]

def amplify_lead(source_lead: str, source_body: str, headline: str) -> str:
    """Prefer a concise verified event summary over padded or duplicate copy."""
    lead=" ".join(source_lead.split())
    if 85<=len(lead)<=185:
        return lead
    if len(lead)>185:
        sentences=meaningful_sentences(lead)
        result=[]
        for sentence in sentences:
            if len(sentence)<18: continue
            if sum(map(len,result))+len(sentence)+len(result)>185: break
            if sentence[:30] in " ".join(result): continue
            result.append(sentence)
        return " ".join(result) if result else lead[:185].rsplit(" ",1)[0]
    from difflib import SequenceMatcher
    for node in BeautifulSoup(source_body,"html.parser").select(
            "section:not(.activity-editorial-context):not(.activity-editorial-explainer) p"):
        for sentence in meaningful_sentences(node.get_text(" ",strip=True)):
            if not 45<=len(sentence)<=155 or not sentence.endswith((".", "!", "?")): continue
            common=SequenceMatcher(None,lead,sentence)
            if common.ratio()>0.4 or (common.find_longest_match(0,len(lead),0,len(sentence)).size
                                      > min(len(lead),len(sentence))*0.52):
                continue
            if len(lead)+len(sentence)+1<=185:
                return lead+" "+sentence
    return lead

def contextual_sections(body: str, category: str, title: str) -> str:
    text = plaintext(body)
    techs = []
    for keyword, explanation in TECH:
        if re.search(r'(?<![A-Za-z0-9])'+re.escape(keyword)+r'(?![A-Za-z0-9])',
                     title+" "+text,flags=re.I):
            techs.append((keyword,explanation))
    if not techs and len(text)<160:
        return ''  # Original has insufficient detail: no invented narrative.
    output = ''
    # Restrict technical background to at most two terms per article, labelled
    # as educational context rather than as verified event-specific activities.
    if techs:
        out=' '.join(expl for _, expl in techs[:2])
        output += '<section class="activity-editorial-explainer"><h2>활동에 등장한 기술 이해하기</h2><p>'+html.escape(out)+'</p></section>'
    if category in TOPIC_CONTEXT and len(text)>=160:
        output += ('<section class="activity-editorial-context"><h2>전공과 진로의 연결</h2><p>'
                   + html.escape(TOPIC_CONTEXT[category]) + '</p></section>')
    return output

def restructure_body(markup: str) -> tuple[str,int]:
    # Reflow only plain-text paragraphs, never caption/link/image markup.
    updates = 0
    pattern = re.compile(r'<p>([^<]{430,})</p>', re.S)
    def rewrite(m):
        nonlocal updates
        sentences=meaningful_sentences(html.unescape(m.group(1)))
        if len(sentences)<3:return m.group(0)
        parts=[]; current=''
        for sen in sentences:
            if current and len(current)+len(sen)>285:
                parts.append(current);current=sen
            else:
                current=(current+" "+sen).strip()
        if current: parts.append(current)
        if len(parts)<=1:return m.group(0)
        updates+=1
        return ''.join('<p>'+html.escape(part)+'</p>' for part in parts)
    return pattern.sub(rewrite,markup),updates

def replace_meta(source: str, attribute: str, key: str, value: str) -> str:
    regex=re.compile(r'(<meta\b(?=[^>]*\b'+attribute+r'="'+re.escape(key)+r'")[^>]*\bcontent=")([^"]*)(")',re.S)
    updated,n=regex.subn(lambda m:m.group(1)+html.escape(value,quote=True)+m.group(3),source,count=1)
    if n!=1:raise RuntimeError(f"Missing meta {attribute}:{key}")
    return updated

def set_markup(source: str, regex: str, value: str, *, esc=True) -> str:
    updated,n=re.subn(regex,lambda m:m.group(1)+(html.escape(value,quote=True) if esc else value)+m.group(3),source,count=1,flags=re.S)
    if n!=1:raise RuntimeError("Missing markup field "+regex)
    return updated

def update_jsonld(source: str, title: str, lead: str, kind: str) -> str:
    def upd(m):
        obj=json.loads(m.group(1))
        if kind=="Article" and obj.get('@type') in ('Article','NewsArticle','BlogPosting'):
            obj['headline']=title
            obj['description']=lead[:220]
        elif kind=="CollectionPage" and obj.get('@type')=="CollectionPage":
            for entry in obj["mainEntity"]["itemListElement"]:
                slug=entry.get('url','').rstrip('/').rsplit('/',1)[-1]
                if slug in TITLES:entry["name"]=TITLES[slug]
        return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+'</script>'
    return SCHEMA.sub(upd,source,count=1)

TITLES={}
LEADS={}
BASELINE_LEADS = {}
try:
    _baseline=json.loads((ROOT/"data"/"activity_editorial_full_review_2026-10-25.json").read_text(encoding="utf-8"))
    BASELINE_LEADS={entry["slug"]:entry.get("lead_after","") for entry in _baseline.get("articles",[])}
except (FileNotFoundError,ValueError):
    pass

LEAD_OVERRIDES = {
    "kopo-727472": "Spring AI 실습 특강에서 LLM과 RAG를 활용하는 인공지능 애플리케이션 개발을 다뤘습니다. ChatGPT와 Llama 등 언어모델의 Spring 기반 서비스 연동 방법을 살펴봤습니다.",
    "kopo-707048": "카카오엔터테인먼트 손성용 개발자가 재학생을 대상으로 객체지향 설계 원칙과 JPA를 중심으로 Spring 실무 개발 사례를 소개했습니다.",
    "kopo-745970": "경력단절여성의 IT 분야 취업 준비를 지원하기 위해 방과후 컴퓨터와 코딩지도사 강사 양성과정을 개강했습니다. 컴퓨터 기초와 코딩 교육을 다루는 과정입니다.",
    "kopo-591393": "2020년 한이음 ICT 공모전에 참가하는 동아리의 소개 카드뉴스를 제작했습니다. 학과의 당시 학생 공모전 참가 활동을 기록한 자료입니다.",
    "kopo-454182": "학과 교육 공간을 제3교육관에서 본관 3층으로 이전했다는 당시의 안내입니다. 현재 강의실 위치는 최신 캠퍼스 안내를 확인해야 합니다.",
    "kopo-727475": "2024년 미래내일 일경험 사업을 통해 퀴즈톡과 함께 추진한 앱 UI/UX 개선 프로젝트의 설명회 기록입니다.",
    "kopo-765578": "학과 1학년과 2학년 학생팀이 2025년 새싹 해커톤 본선에 진출했습니다. AI 기반 서비스의 기획과 구현을 중심으로 대회에 참여한 활동입니다.",
}

def main():
    content=ARCHIVE.read_text(encoding="utf-8")
    cards=CARD.findall(content)
    if len(cards)!=286:raise RuntimeError("Archive must contain 286 current cards")
    details={}
    counts=Counter()
    for card in cards:
        match=re.search(r'<h3><a href="/activities/([^/]+)/">([^<]*)</a></h3>',card)
        if not match:raise RuntimeError("Malformed archive card")
        slug=match.group(1)
        file=ROOT/'activities'/slug/'index.html'
        original=file.read_text(encoding='utf-8')
        if not file.exists():raise RuntimeError("Detail page missing: "+slug)
        lead=re.search(r'<p class="activity-lead">(.*?)</p>',original,re.S)
        if lead is None:raise RuntimeError("Missing lead "+slug)
        source_lead=html.unescape(plaintext(lead.group(1)))
        body_match=BODY.search(original)
        if body_match is None:raise RuntimeError("Missing editorial body "+slug)
        body=body_match.group(2)
        plain_body=BeautifulSoup(body,"html.parser")
        for note in plain_body.select(".activity-editorial-explainer,.activity-editorial-context"):
            note.decompose()
        before_body_chars=len(" ".join(plain_body.stripped_strings))
        # Site-generated presentation previously overlaid some curated title/lead
        # overrides; explicitly consolidate those into source pages.
        present_title=CURATED.get(slug,(html.unescape(match.group(2)),source_lead))[0]
        new_title=clean_title(OVERRIDES.get(slug,present_title))
        if len(new_title)<14:
            # Add only the verifiable publication year, never a fictitious result.
            published = re.search(r'<time datetime="(\d{4})-\d\d-\d\d"',card)
            yr = published.group(1) if published else ''
            if yr and not new_title.startswith(yr):
                new_title=clean_title(yr+'년 '+new_title)
            if len(new_title)<14:
                new_title=clean_title(new_title+', 학과 활동 기록')
        for phrase in STOP_PHRASES:body=body.replace(phrase,'')
        if slug in FACT_CORRECTIONS:
            pattern,repl=FACT_CORRECTIONS[slug]
            body,n=re.subn(pattern,lambda m:repl,body,count=1,flags=re.S)
            if n:counts['factual_repairs']+=1
        body,split=restructure_body(body)
        if split:counts['long_paragraphs_split']+=split
        # Intro includes only existing factual sentences from the original page.
        curated_lead=CURATED.get(slug,(None,source_lead))[1]
        seed=curated_lead if slug in CURATED else BASELINE_LEADS.get(slug,source_lead)
        seed=LEAD_OVERRIDES.get(slug,seed)
        new_lead=seed if slug in LEAD_OVERRIDES else amplify_lead(seed,body,new_title)
        # Only provide editorial context for categories with original evidence.
        cat_match=re.search(r'<p class="activity-kicker">DEPARTMENT ACTIVITIES · (.*?)</p>',original,re.S)
        category=html.unescape(cat_match.group(1)) if cat_match else ''
        card_cat=re.search(r'<div class="activity-card-meta"><span>([^<]+)</span>',card)
        if card_cat:category=html.unescape(card_cat.group(1))
        if re.search(r'class="activity-editorial-(?:context|explainer)"',body):
            counts["contextual_expansions_present"]+=1
        if not re.search(r'class="activity-editorial-(?:context|explainer)"',body):
            expansion=contextual_sections(body,category,new_title)
            if expansion:
                body += '\n' + expansion
                counts['contextual_expansions']+=1
            else:
                counts['thin_source_no_invention']+=1
        if before_body_chars<240:counts['original_under_240_chars']+=1
        TITLES[slug]=new_title;LEADS[slug]=new_lead
        new_page=original
        new_page=new_page[:body_match.start(2)]+body+new_page[body_match.end(2):]
        new_page=set_markup(new_page,r'(<h1>)(.*?)(</h1>)',new_title)
        new_page=set_markup(new_page,r'(<title>)(.*?)(</title>)',new_title+' | 빅데이터소프트웨어공학과')
        new_page=set_markup(new_page,r'(<p class="activity-lead">)(.*?)(</p>)',new_lead)
        for attr,key,val in (
            ('name','description',new_lead[:165]),
            ('property','og:title',new_title+' | 빅데이터소프트웨어공학과'),
            ('property','og:description',new_lead[:200]),
            ('name','twitter:title',new_title+' | 빅데이터소프트웨어공학과'),
            ('name','twitter:description',new_lead[:200]),
        ):
            new_page=replace_meta(new_page,attr,key,val)
        new_page=re.sub(r'(\balt=")학과 활동 현장 사진(")',
                        lambda m:m.group(1)+html.escape(new_title+' 관련 현장 사진',quote=True)+m.group(2),new_page)
        new_page=update_jsonld(new_page,new_title,new_lead,'Article')
        if (re.findall(r'\bsrc="([^"]+)"',new_page)!=re.findall(r'\bsrc="([^"]+)"',original) or
            re.findall(r'\bhref="([^"]+)"',new_page)!=re.findall(r'\bhref="([^"]+)"',original)):
            raise RuntimeError("Source media or links changed for "+slug)
        original_date=re.search(r'property="article:published_time" content="([^"]+)"',original)
        modified_date=re.search(r'property="article:published_time" content="([^"]+)"',new_page)
        if original_date and (not modified_date or original_date.group(1)!=modified_date.group(1)):
            raise RuntimeError("Article date changed "+slug)
        if new_page!=original:
            file.write_text(new_page,encoding='utf-8')
            counts['detail_pages_changed']+=1
        if new_title!=html.unescape(match.group(2)):counts['titles_changed']+=1
        if new_lead!=source_lead:counts['intros_changed']+=1
        details[slug]={'date':modified_date.group(1) if modified_date else '',
                       'title_before':html.unescape(match.group(2)),'title_after':new_title,
                       'source_chars':before_body_chars,
                       'final_body_chars':len(plaintext(body)),
                       'expanded':bool(re.search(r'class="activity-editorial-(?:context|explainer)"',body))}
    # Update cards in the *original* archive, not just the compiled site.
    def update_card(m):
        card=m.group(0)
        slug=re.search(r'<h3><a href="/activities/([^/]+)/"',card).group(1)
        title,lead=TITLES[slug],LEADS[slug]
        card=set_markup(card,r'(<h3><a href="[^"]+">)(.*?)(</a></h3>)',title)
        card=set_markup(card,r'(</h3><p>)(.*?)(</p>)',lead[:230])
        card=re.sub(r'(\baria-label=")[^"]*(")',lambda n:n.group(1)+html.escape(title+' 자세히 보기',quote=True)+n.group(2),card,count=1)
        card=re.sub(r'(\balt=")학과 활동 현장 사진(")',lambda n:n.group(1)+html.escape(title+' 관련 현장 사진',quote=True)+n.group(2),card)
        return card
    revised=CARD.sub(update_card,content)
    revised=update_jsonld(revised,'','','CollectionPage')
    if len(CARD.findall(revised))!=286:raise RuntimeError("Card count changed")
    ARCHIVE.write_text(revised,encoding='utf-8')
    JSON_REPORT.parent.mkdir(parents=True,exist_ok=True)
    JSON_REPORT.write_text(json.dumps({'date':'2026-10-25','count':286,'stats':dict(counts),'articles':details},
                    ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=[
        '# 학과 활동 기사 제목 통일 및 본문 보완 결과',
        '',
        '기준: 제목은 쉼표 중심의 일관된 문장형으로 통일하고, 공식 기술명 표기는 보존합니다.',
        '본문은 기존 원문에서 확인되는 사실, 기사에 실제 등장한 기술의 개념 설명, '
        '전공·진로에 대한 편집자 해설을 분리해 보완합니다. 확인되지 않은 현장 사실을 생성하지 않습니다.',
        '',
        '| 항목 | 건수 |','|---|---:|',
        *[f'| {k} | {v} |' for k,v in sorted(counts.items())],
        '',
        '## 원본 정보가 적어 추가 취재가 필요한 게시물',
        '',
    ]
    for slug,d in details.items():
        if d['source_chars']<240:
            report.append(f'- [{d["title_after"]}](https://ai.k-bigdata.kr/activities/{slug}/), 기존 본문 {d["source_chars"]}자')
    report.extend(['','## 제목 변경 내역','','| 원래 제목 | 변경 제목 |','|---|---|'])
    for slug,d in details.items():
        if d['title_before']!=d['title_after']:
            report.append('| '+d['title_before'].replace('|','/')+' | '+d['title_after'].replace('|','/')+' |')
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text('\n'.join(report)+'\n',encoding='utf-8')
    print('ARTICLE_EDITORIAL_PASS',json.dumps(dict(counts),ensure_ascii=False),flush=True)
    print('ARTICLE_EDITORIAL_SHORTEST',json.dumps(
       sorted([(d['source_chars'],slug) for slug,d in details.items()])[:12],
       ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
