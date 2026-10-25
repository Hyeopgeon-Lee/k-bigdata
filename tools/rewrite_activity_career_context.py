#!/usr/bin/env python3
"""Rewrite career relevance in every department activity article with verified,
event-specific employment and portfolio implications. No hiring guarantees,
invented placements, fictitious skills, or unverifiable direct participation.
"""
from __future__ import annotations
import html
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "activities/index.html"
REPORT = ROOT / "reports/activity_career_context_review_2026-10-25.md"
DETAIL = ROOT / "data/activity_career_context_review_2026-10-25.json"
CARDS = re.compile(r'<article class="activity-card">(.*?)</article>', re.S)
CONTEXT = re.compile(
    r'<section class="activity-editorial-context">\s*<h2>전공과 진로의 연결</h2>\s*<p>.*?</p>\s*</section>',
    re.S,
)
TAG = re.compile(r'<[^>]*>')
CAREER_CATEGORIES = {
    "수상·성과", "취업·진로", "멘토링·진로", "전문가 특강",
    "진로체험", "교원 연수", "학생 프로젝트", "연구·학술",
    "산학협력", "사회공헌·봉사", "지역사회 교육", "학과 행사",
    "학과 소식", "과거 기록", "기술·참고자료",
}
# Technologies determine only an *appropriate potential career path*.
# They are not asserted as technologies used by a named participant.
ROLE_MATCHES = [
    (r"K-PaaS|PaaS-TA|쿠버네티스|Kubernetes|클라우드|Cloud|DevOps|MSA|마이크로서비스|Docker|리눅스|Rocky Linux|Ubuntu", "클라우드·플랫폼·백엔드 개발"),
    (r"LangChain|LangGraph|LLM|RAG|생성형 AI|언어모델|비전언어모델|자연어처리|OCR|이미지 인식|인공지능|AI 에이전트", "AI 응용·소프트웨어 개발"),
    (r"OpenCV|영상처리|컴퓨터비전|얼굴 인식|이미지 분류", "컴퓨터비전·AI 개발"),
    (r"Spark|Hadoop|맵리듀스|데이터 파이프라인|데이터 압축|데이터엔지니어|빅데이터 처리", "데이터 엔지니어링"),
    (r"RStudio|통계|데이터 분석|데이터 시각화|소셜데이터|SNS분석|소셜 빅데이터|빅데이터|SNS 데이터", "데이터 분석·시각화"),
    (r"Spring|Java|JPA|MyBatis|MariaDB|SQL|DB|웹 API|웹 개발|서버 개발", "백엔드·데이터베이스 개발"),
    (r"Flutter|앱 개발|모바일|UI/UX|React|Vue|프론트엔드|웹디자인", "프론트엔드·모바일 서비스 개발"),
    (r"보안|정보보호|암호화|블록체인", "정보보안·서비스 개발"),
]
HAND_EDITED = {
 "sesac-hackathon-grand-prize-2025":
    "서울시 새싹 해커톤 대상은 AI 서비스를 기획하고 제한된 시간 안에 구현한 결과를 외부 평가에서 인정받았다는 성과입니다. 수상 증빙과 서비스 시연 화면, 팀에서 맡은 기능, 코드와 문제 해결 과정을 함께 정리하면 AI·소프트웨어 개발 직무에 제출할 완성도 높은 포트폴리오가 됩니다. 수상 실적에 구현 근거를 더하면 우수 IT 기업의 서류 전형과 기술면접에서 경쟁력을 설명하기 좋습니다.",
 "kopo-699006":
    "K-PaaS 기반 여행지 추천 서비스로 전국 1위와 과기정통부 장관상을 받은 이력은 클라우드·AI 융합 개발 포트폴리오의 강력한 근거가 됩니다. MSA 설계, 리뷰 감정분석, 일정 추천 기능을 각각 어떤 문제 해결에 적용했는지 도식과 실행 화면으로 보여주면 클라우드 엔지니어·백엔드·AI 개발 직무 지원 시 기술 선택 이유와 구현 역량을 구체적으로 설명할 수 있습니다.",
 "kopo-711758":
    "AI 실종자 찾기 서비스로 K-PaaS 공모전 대상을 수상한 경험은 공공 문제를 기술로 해결한 사례입니다. 얼굴 예측 기능의 역할과 클라우드 배포 구조, 담당 기능, 시연 결과를 정리하면 AI 응용 개발과 클라우드 서비스 직무 지원에 활용할 수 있습니다. 공모전 수상 자체뿐 아니라 완성된 서비스를 어떻게 구현하고 검증했는지가 포트폴리오의 차별점입니다.",
 "kopo-738804":
    "ACK 2024 동상 수상 논문은 데이터 압축 방식에 따른 맵리듀스 처리 성능을 직접 비교한 연구 성과입니다. 실험 환경, 비교 기준, 측정 결과와 기여 내용을 포트폴리오에 정리하면 데이터 엔지니어·분산처리 개발 직무의 기술면접에서 성능 검증 역량을 보여줄 수 있습니다. 논문과 수상 증빙은 연구 결과를 객관적으로 제시하는 자료가 됩니다.",
 "kopo-738801":
    "ACK 2024 논문경진대회 동상은 학생·교수 공동연구의 외부 수상 실적입니다. 공동연구에서 다룬 문제와 본인의 기여, 실험 방법, 결과를 수상 증빙과 함께 포트폴리오에 정리하면 연구를 실제 개발·데이터 분석 문제에 적용할 수 있음을 설명하는 자료가 됩니다. 데이터 엔지니어링이나 연구개발 직무를 준비할 때 특히 활용도가 높습니다.",
 "kopo-763327":
    "비전언어모델 기반 얼굴 초해상도 연구로 ACK 2025 동상을 받은 성과는 AI 모델 연구 역량을 보여줄 수 있는 대외 실적입니다. 사용한 데이터, 비교 모델, 평가 방법, 본인 기여를 정리하면 컴퓨터비전·AI 개발 직무 포트폴리오의 신뢰도를 높이고, 기술면접에서 모델 성능과 한계를 설명하는 근거가 됩니다.",
 "kopo-762210":
    "프로젝트경진대회 우수상과 장려상은 AI·클라우드 모의투자 서비스와 소비 데이터 시각화 앱의 구현 결과를 보여주는 자료입니다. 학생별 담당 기능, 실행 화면, 시스템 구조, 데이터 처리 과정을 작품별 포트폴리오로 정리하면 금융 IT·데이터 분석·웹 개발 직무 지원에 활용할 수 있습니다. 수상 이력에 실제 구현 내용을 결합하는 것이 중요합니다.",
 "kopo-777680":
    "효성ITX 현직자가 강조한 문제 해결력, 협업, 기술 변화에 대한 학습 태도는 신입 IT 인재 채용에서 준비해야 할 역량입니다. 재학생은 팀 프로젝트에서 발생한 오류와 해결 방법, 맡은 역할, 협업 과정을 포트폴리오에 남기고 자기소개서·기술면접 사례로 발전시킬 수 있습니다. 특강에서 제시한 인재상과 지원 기업의 채용 요건을 비교하는 것이 취업 준비의 핵심입니다.",
 "kopo-773576":
    "엔씨IDS에서 근무하는 졸업생의 학습·프로젝트·취업 준비 경험은 후배들이 기업 실무를 기준으로 준비할 항목을 정하는 데 의미가 있습니다. 지원하려는 개발 직무에 맞춰 프로젝트의 담당 기능, 코드 품질, 협업 사례를 포트폴리오와 자기소개서에 정리하고 면접 답변까지 연결하는 것이 실질적인 활용 방법입니다.",
 "kopo-770067":
    "LangChain·LangGraph·LangSmith를 다룬 졸업생 특강은 최근 AI 응용 개발 직무를 준비하는 학생에게 실무형 포트폴리오의 방향을 제시합니다. 도구 호출 흐름, 상태 관리, 평가·오류 처리 기능을 갖춘 에이전트를 직접 구현해 동작 화면과 저장소, 설계 이유를 설명할 수 있다면 AI 서비스 개발 직무의 기술면접에서 활용할 수 있습니다.",
 "gangseo-job-fair-2026":
    "2학년 학생들의 취업박람회 참여는 실제 채용기업이 요구하는 기술과 직무를 확인하는 자리였습니다. 관심 기업의 모집 직무와 기술 스택을 비교해 이력서의 핵심 역량을 조정하고, 자신의 프로젝트에서 해당 기술을 적용한 근거를 포트폴리오 첫 부분에 배치하면 지원 직무에 맞는 취업 준비로 이어집니다. 채용정보를 확인했다는 사실보다 이후 지원·면접 준비에 반영하는 과정이 중요합니다.",
 "department-funding-2025":
    "약 10억 원 규모의 실습환경 개선은 AI·데이터·클라우드 개발에 필요한 장비와 환경을 강화하기 위한 투자입니다. 학생들이 GPU 활용 실험, 데이터 처리, 서비스 배포 과정을 직접 수행하고 결과를 포트폴리오로 남기면 기업이 요구하는 개발·운영 경험을 구체적으로 보여줄 수 있습니다. 투자 자체가 취업을 보장하는 것은 아니며 실제 프로젝트 수행 결과가 경쟁력을 만듭니다.",
 "department-reorganization-2025":
    "AI·소프트웨어 개발·클라우드 실습을 강화하는 학과 개편은 학생이 준비할 IT 직무를 넓히는 교육 방향입니다. 백엔드 API 개발, AI 활용 서비스, 클라우드 배포 중 희망 직무와 연결되는 프로젝트를 선택하고 코드·아키텍처·테스트 결과를 정리하면 채용기업에 제출할 직무 중심 포트폴리오를 구성할 수 있습니다.",
 "alumni-ha-jae-hyeong-lecture-2026":
    "부산대 대학원에 진학한 졸업생의 사례는 IT 개발 직무 취업뿐 아니라 연구개발 중심의 경력 설계도 고려할 수 있음을 보여줍니다. 대학원 진학을 생각한다면 학부 프로젝트의 연구 주제, 실험 과정, 성과를 정리해 연구계획서·포트폴리오에 연결하고, 취업을 준비한다면 같은 프로젝트에서 구현한 코드와 담당 역할을 강조할 수 있습니다.",
 "kopo-746370":
    "KB데이타시스템에서 데이터 엔지니어로 일하는 졸업생의 경험은 금융 IT 기업에 지원할 때 준비해야 할 직무 역량을 가늠하는 사례입니다. SQL·데이터 처리 과제와 프로젝트 수행 과정, 장애 해결 경험을 정리해 금융 데이터 처리 직무에 맞는 포트폴리오와 면접 답변을 준비하는 데 연결할 수 있습니다.",
 "kopo-757516":
    "오케스트로와의 클라우드·K-PaaS 산학협력은 교육 주제를 기업의 플랫폼 기술 수요와 연결할 수 있는 기반입니다. 학생 입장에서는 클라우드 배포, 서비스 운영, 장애 대응을 보여주는 프로젝트가 플랫폼·DevOps 직무 지원에서 중요한 자료가 됩니다. 협약 사실을 채용 확정으로 표현하기보다 실제 기업 연계 교육과 학생 결과물로 성과를 보여주는 것이 정확합니다.",
 "teacher-generative-ai-r-training-2026":
    "생성형 AI와 R을 주제로 고교 교사 대상 실습 연수를 운영한 경험은 학과의 AI·데이터 교육 역량을 보여줍니다. 학생 취업과의 연결점은 연수 개최 자체보다 데이터 수집·분석과 AI 도구 활용을 실제 개발 과제로 구현하는 데 있습니다. 재학생이 분석 코드, 시각화 결과, 해석 과정을 포트폴리오로 정리하면 데이터 분석·AI 응용 직무 준비에 활용할 수 있습니다.",
 "teacher-ai-llm-workshop-2026":
    "Python·머신러닝·CNN을 활용한 교원 연수 주제는 AI 개발 직무에 필요한 기본 실습과 맞닿아 있습니다. 학과의 교육 운영 경험을 바탕으로 재학생이 이미지 분류 모델의 데이터 구성, 학습 결과, 성능 평가와 오류 사례를 정리한다면 AI 개발 직무 포트폴리오로 발전시킬 수 있습니다. 교원 연수 참가자의 취업 성과와는 구분해야 합니다.",
 "kopo-443890":
    "교남 소망의 집에서 진행한 컴퓨터 유지보수와 시설 지원은 IT 기술을 지역사회 문제 해결에 적용한 경험입니다. 본인이 담당한 점검·수리 내용을 사실에 근거해 정리한다면 IT 서비스 운영·기술지원 직무 면접에서 사용자 대응과 책임감을 보여주는 사례로 활용할 수 있습니다. 봉사활동 자체를 전문 개발 경력으로 과장하지 않는 것이 중요합니다.",
}
def clean_text(value: str) -> str:
    return " ".join(html.unescape(TAG.sub(" ",value)).split())

def role_for(title: str, actual_body: str) -> str:
    # A number of archived posts end with generic AI/cloud promotional copy.
    # Ignore that copy when choosing a specific career title.
    for focus in (title, actual_body[:125]):
        for pattern,job in ROLE_MATCHES:
            if re.search(pattern,focus,re.I):
                return job
    return "소프트웨어·데이터 관련"

def topic_from_title(title: str) -> str:
    # Preserve distinguishing details after the comma; otherwise several
    # different Java mentoring activities collapse into identical career copy.
    subject=title.strip()
    return subject if len(subject)<=68 else subject[:65].rstrip()+"…"

def result_detail(title: str, actual: str) -> str:
    if re.search("논문|학술|연구",title):
        return "연구 주제와 실험 방법, 본인의 기여, 결과를 정리한 논문·발표 자료"
    if re.search("AI|LLM|인공지능|모델|자연어",title):
        return "AI 모델이나 서비스의 입력·출력, 평가 결과, 담당 기능을 담은 코드와 시연 자료"
    if re.search("클라우드|PaaS|MSA|DevOps",title):
        return "서비스 아키텍처, 클라우드 배포 과정, 담당 기능을 보여주는 코드와 시연 자료"
    if re.search("빅데이터|데이터|분석",title):
        return "데이터 수집·정제·분석 방법과 결과를 담은 코드·시각화 자료"
    if re.search("앱|웹|소프트웨어|SW|해커톤|프로젝트",title):
        return "핵심 기능과 사용자 문제, 담당 부분, 동작 화면을 정리한 프로젝트 결과물"
    return "주제 선택과 수행 과정, 맡은 역할과 최종 결과를 설명한 프로젝트 증빙 자료"

def generate_career_text(slug: str, title: str, category: str, actual: str, lead: str="") -> str | None:
    """One short, specific, practical employment takeaway; no invented outcome."""
    if slug in HAND_EDITED:
        return HAND_EDITED[slug]
    topic=topic_from_title(title)
    roles=role_for(title,actual)
    awards=bool(re.search(r"수상|대상|동상|장려상|우수상|최우수상|전국 1위|감사장|1등|2위|3위",title))
    is_student=bool(re.search("학생|재학생|졸업생|프로젝트|공모전",title+" "+lead))
    sports=bool(re.search("운동회|피구|줄다리기|풋살|축제|산책|체육|다과회|친목",title))
    faculty=bool(re.search("교수|교원|학회|논문지|국제학술",title))
    if sports:
        return (f"‘{topic}’ 활동은 전공 개발 프로젝트나 채용 성과 자체는 아닙니다. 다만 팀의 공동 목표를 위해 역할을 나누고 의견을 조율한 경험은 "
                "취업 면접의 협업·갈등 해결 질문에서 구체적인 사례로 활용할 수 있습니다. 실제 맡은 역할과 행동을 설명하는 것이 중요하며, 기술 포트폴리오는 별도의 개발 작품으로 준비해야 합니다.")
    if category=="수상·성과":
        if re.search("감사장|봉사",title):
            return (f"‘{topic}’ 성과는 지역사회와의 신뢰 관계를 보여주는 자료입니다. 활동 당시 본인이 맡은 역할과 현장 문제를 해결한 과정을 "
                    "취업 자기소개서의 책임감·협업 사례로 정리할 수 있습니다. 다만 전문 기술력을 입증하는 자료는 개발 프로젝트와 별도로 준비하는 것이 좋습니다.")
        if faculty and (re.search("교수|학과장",title) and not re.search("학생|재학생|졸업생",title) or not is_student):
            return (f"‘{topic}’ 수상은 교수진의 연구 역량과 학과의 전문성을 보여줍니다. 학생들이 이와 관련된 주제로 연구·개발 프로젝트를 수행한다면 "
                    f"{roles} 직무에 맞는 실험 결과와 구현 과정을 포트폴리오에 담을 수 있습니다. 교수진의 수상 실적을 학생 개인의 취업 성과로 표현해서는 안 됩니다.")
        detail=result_detail(title,actual)
        if awards:
            return (f"‘{topic}’은 대외 평가에서 인정받은 성과로, 취업 포트폴리오에 수상 증빙을 제시할 수 있는 이력이 됩니다. "
                    f"{detail}를 함께 준비하면 {roles} 직무 지원 시 단순한 참가 경력이 아니라 실무형 문제 해결 역량을 설명할 수 있습니다. "
                    "채용기업의 서류 심사와 기술면접에서 자신의 기여를 구체적으로 보여주는 것이 수상 이력의 실질적인 가치입니다.")
        return (f"‘{topic}’에 참여한 경험은 공모전에서 기술을 적용하고 결과물을 준비한 과정으로 정리할 수 있습니다. "
                f"{detail}와 참가 기록을 함께 담으면 {roles} 직무 포트폴리오의 한 부분이 됩니다. "
                "수상 여부와 관계없이 실제 맡은 일과 구현 수준을 정확하게 보여주는 것이 취업 준비에 중요합니다.")
    if category=="학생 프로젝트" or (category=="학과 행사" and re.search("작품|프로젝트|앱|경진대회|개발",title)):
        detail=result_detail(title,actual)
        return (f"‘{topic}’ 활동에서 확인되는 작품이나 개발 경험은 {roles} 직무를 준비하는 학생에게 포트폴리오 소재가 됩니다. "
                f"{detail}에 README, 실행 방법, 문제 해결 기록을 더하면 채용 담당자가 지원자의 실제 구현 범위를 판단하기 쉽습니다. "
                "팀 프로젝트라면 전체 기능보다 본인이 설계·구현한 부분을 명확히 밝히는 것이 중요합니다.")
    if category=="멘토링·진로":
        if re.search("졸업생|재직|취업|기업|대학원 진학",title):
            return (f"‘{topic}’에서 소개된 선배의 진로 경험은 지원 기업과 직무를 정하는 데 참고할 만합니다. "
                    f"희망하는 {roles} 직무의 채용 요건을 살펴보고 선배가 강조한 학습·프로젝트 준비 내용을 자신의 기술 스택과 비교해 "
                    "이력서, 포트폴리오, 면접 답변의 보완 항목으로 구체화할 수 있습니다.")
        return (f"‘{topic}’ 멘토링에서 다룬 학습 내용을 작은 구현 결과물로 만들어 두면 {roles} 직무 준비에 활용할 수 있습니다. "
                "수업 코드 자체보다 스스로 기능을 확장한 부분, 오류를 해결한 과정, 다른 사람에게 설명할 수 있는 근거를 "
                "GitHub와 README에 기록해 포트폴리오의 기초를 쌓는 것이 좋습니다.")
    if category=="취업·진로":
        if re.search("부스|시연|체험",title) and re.search("박람회|AI|소셜|데이터",title):
            return (f"‘{topic}’에서 소개한 데이터 분석·AI 시연은 전공 기술을 일반 방문자에게 설명하는 현장 경험으로 연결됩니다. "
                    "실제로 부스를 준비하거나 운영한 학생이라면 자신이 맡은 데이터 처리, 화면 구성, 발표·시연 역할과 방문자 질문에 대응한 사례를 정리해 "
                    f"{roles} 직무 포트폴리오와 기술면접에 활용할 수 있습니다. 단순 행사 방문과 직접 개발·운영한 경험은 구분해야 합니다.")
        if re.search("박람회|채용|취업설명회|기업 탐방|직무 탐색",title):
            return (f"‘{topic}’에서 얻은 채용·직무 정보는 실제 입사지원 전략으로 이어져야 합니다. "
                    f"관심 기업의 {roles} 직무 요건을 비교한 뒤 자신의 프로젝트 경험 중 적합한 기술·성과를 이력서와 포트폴리오 앞부분에 배치하고 "
                    "부족한 역량은 다음 프로젝트나 면접 준비 과제로 정리할 수 있습니다.")
        if re.search("인턴십|일경험|실습",title):
            return (f"‘{topic}’은 기업에서 요구하는 업무 방식과 학생의 실습 경험을 연결할 수 있는 기회입니다. "
                    f"실제 참여한 학생은 맡은 업무 범위와 도구, 문제 해결 과정, 검증 가능한 결과를 기록해 {roles} 직무 취업 포트폴리오에 활용할 수 있습니다. "
                    "사업 선정이나 참여 안내만으로 개인의 인턴십 수행·취업을 확정해 설명해서는 안 됩니다.")
        return (f"‘{topic}’의 핵심은 채용에서 평가하는 요소를 미리 파악하고 준비할 수 있다는 점입니다. "
                f"{roles} 직무에 맞는 프로젝트·기술 경험을 추려 자기소개서의 문제 해결 사례로 쓰고, 면접에서 본인의 역할과 성과를 "
                "코드·시연 결과를 근거로 설명하도록 준비하면 좋습니다.")
    if category=="전문가 특강":
        if re.search("취업|인재상|면접|자기소개서|포트폴리오",title):
            return (f"‘{topic}’에서 다룬 기업의 인재상과 실무 요구사항은 지원 직무에 맞는 자기소개서·포트폴리오를 준비하는 기준이 됩니다. "
                    "프로젝트에서 실제 담당한 일과 해결한 오류, 협업 사례를 골라 채용 공고의 요구 역량과 일치시키고 "
                    "기술면접에서 설계 이유를 설명할 수 있도록 정리하는 것이 효과적입니다.")
        return (f"‘{topic}’에서 소개한 기술과 현장 사례를 실제로 구현해 본다면 {roles} 직무에 지원할 때 보여줄 결과물이 생깁니다. "
                "특강을 들었다는 이력만 적기보다 핵심 기능을 직접 실습·확장해 코드와 실행 화면을 남기고 "
                "기술을 선택한 이유, 어려웠던 점, 해결 방법을 포트폴리오와 면접 답변으로 발전시키는 것이 중요합니다.")
    if category=="산학협력":
        if re.search("MOU|협약|업무협약|협력",title):
            return (f"‘{topic}’은 학과 교육 방향을 산업체가 필요로 하는 기술 역량과 연결할 수 있는 협력 사례입니다. "
                    f"학생에게 실질적인 취업 경쟁력이 되려면 {roles} 분야의 기업 과제나 실습을 직접 수행하고 "
                    "담당 기능·결과를 포트폴리오로 남기는 과정이 필요합니다. 협약 체결만으로 채용이나 현장실습이 보장되는 것은 아닙니다.")
        return (f"‘{topic}’에서 다룬 현장 기술 과제는 {roles} 직무가 어떤 문제를 해결하는지 보여주는 자료입니다. "
                "학생들이 같은 유형의 문제를 프로젝트로 재현하고 요구사항, 구현 방법, 테스트 결과를 기록하면 "
                "기업 지원 때 실무 이해도를 설명할 수 있는 포트폴리오로 연결할 수 있습니다.")
    if category=="연구·학술":
        if faculty and (re.search("교수|학과장",title) and not re.search("학생|재학생|졸업생",title) or not is_student):
            return (f"‘{topic}’ 연구는 학과 교수진의 연구 주제와 기술 전문성을 보여줍니다. "
                    f"학생 개인의 직접적인 연구 실적으로 간주하기보다는 관련 기술을 학습하고 실험·구현 결과를 스스로 만들어 {roles} 직무에 맞는 "
                    "포트폴리오로 발전시키는 것이 취업 준비에 의미가 있습니다.")
        return (f"‘{topic}’의 연구·발표 경험은 주제를 정의하고 데이터를 다루거나 성능을 검증한 과정을 보여줄 수 있습니다. "
                f"본인의 연구 기여, 실험 설계와 결과를 논문·발표자료와 함께 정리하면 {roles} 직무의 연구개발·기술면접에서 "
                "본인의 문제 해결 과정을 구체적으로 제시할 수 있습니다.")
    if category=="교원 연수" or (category=="진로체험" and re.search("교원|교사.*연수|교직원",title)):
        return (f"‘{topic}’은 학과가 {roles} 분야의 기술을 실습 중심으로 교육할 수 있음을 보여주는 사례입니다. "
                "교원 연수의 성과를 학생 취업 성과로 혼동해서는 안 되며, 재학생이 유사한 기술로 분석 코드·서비스·모델을 직접 구현하고 "
                "실행 결과를 포트폴리오로 남길 때 해당 직무 준비에 연결될 수 있습니다.")
    if category=="진로체험":
        return (f"‘{topic}’은 참가자가 데이터·소프트웨어 분야의 직무를 접하는 진로 탐색 활동입니다. "
                f"체험에서 다룬 기술을 이후 학습으로 확장하고 작은 프로젝트로 구현하면 {roles} 분야 진학과 장기적인 취업 준비의 출발점이 됩니다. "
                "일회성 체험을 전문 개발 경력으로 표현하기보다는 실제로 만든 결과물을 중심으로 역량을 발전시키는 것이 중요합니다.")
    if category=="지역사회 교육" or (category=="취업·진로" and re.search("여성|코딩지도사|재취업",title)):
        if re.search("지도사|방과후|취업|재취업",title):
            return (f"‘{topic}’ 과정은 컴퓨터 활용과 코딩 교육을 익혀 관련 교육·지도 업무를 준비하는 사람에게 직접적인 진로 탐색 기회가 됩니다. "
                    "취업 준비에서는 수업 시연안, 실습 과제, 지도 방법 등을 자신의 수행 결과로 정리해 교육기관·방과후 교육 채용에 활용할 수 있습니다.")
        return (f"‘{topic}’에서 다룬 교육 내용을 직접 실행한 코드나 학습 결과로 정리하면 {roles} 분야로 진입하기 위한 학습 이력을 만들 수 있습니다. "
                "학습 단계에서 익힌 개념과 완성한 결과물, 추가로 보완할 기술을 구분하여 정리하는 것이 이후 직무 교육과 취업 준비에 유용합니다.")
    if category=="사회공헌·봉사":
        if re.search("컴퓨터 유지보수|SW동아리|소프트웨어 개발|기술봉사|수리|설치",title+" "+actual[:145]):
            return (f"‘{topic}’에서 수행한 기술 지원이나 재능기부 활동은 현장 사용자의 문제를 이해한 경험으로 정리할 수 있습니다. "
                    "직접 맡은 점검·설치·개발 업무와 해결 과정을 사실대로 기록하면 IT 서비스 운영·기술지원 직무의 고객 대응·문제 해결 사례로 활용할 수 있습니다. "
                    "봉사 이력만으로 전문 개발 경험을 입증했다고 표현하지는 않는 것이 적절합니다.")
        return (f"‘{topic}’은 개발 기술을 검증하는 프로젝트라기보다 책임감과 지역사회 참여를 보여주는 활동입니다. "
                "취업 자기소개서나 인성면접에서는 본인이 맡은 역할과 협업·소통 사례를 설명하는 자료가 될 수 있습니다. "
                "IT 직무의 기술 역량은 별도 프로젝트 및 자격·실습 결과로 입증해야 합니다.")
    if category=="학과 행사":
        if re.search("교수|논문|학술대회|연구 발표|연구 성과",title):
            return (f"‘{topic}’은 학과의 연구·기술 성과를 소개하는 활동입니다. 교수진의 연구를 학생 개인 성과로 표현해서는 안 되며, "
                    f"재학생이 해당 주제로 직접 실험하거나 코드를 구현하고 결과를 기록하면 {roles} 분야의 연구개발·기술 직무에 지원할 "
                    "포트폴리오를 준비할 수 있습니다.")
        if re.search("코딩지도사|방과후 컴퓨터|여성 재취업|교육과정 수료",title):
            return (f"‘{topic}’에서 운영한 교육은 참여자의 취업·재취업 준비와 관련됩니다. 수료 이력에 더해 실습 결과, "
                    "코딩 지도용 수업안, 과제 수행 내용을 직접 정리하면 방과후 교육·IT 교육지원 직무 지원 때 설명할 자료가 됩니다. "
                    "수료 자체와 실제 취업 성과는 구분해야 합니다.")
        if re.search("취업박람회|일자리박람회|채용박람회|취업 설명회",title):
            return (f"‘{topic}’은 채용 현장과 IT 진로를 소개한 행사입니다. "
                    f"관련 {roles} 분야의 채용공고를 확인해 본인의 구현 경험을 이력서·포트폴리오에 연결하고, "
                    "체험부스 운영 경험이 있다면 설명·시연을 맡은 역할과 질문에 대응한 사례를 면접 준비에 활용할 수 있습니다.")
        if re.search("고등학생|중학생|진로체험|코딩 체험|AI 교육|학생교육|교육캠퍼스",title):
            return (f"‘{topic}’은 예비 진학자에게 IT 기술과 관련 직무를 소개하는 활동입니다. "
                    "재학생의 실제 취업 경쟁력은 이런 행사를 운영했다는 기록만으로 생기는 것이 아니라, 교육 콘텐츠나 시연 프로그램을 직접 "
                    "설계·구현한 경험을 구체적인 역할·코드·결과물로 정리할 때 드러납니다.")
        if re.search("GPU|워크스테이션|교육환경|학과 개편|실습실|AI|빅데이터|클라우드",title):
            return (f"‘{topic}’에서 소개된 교육환경과 실습 주제는 {roles} 분야의 직무 준비와 연결할 수 있습니다. "
                    "채용에서 의미 있는 것은 장비 보유나 행사 참가 그 자체가 아니라 학생이 직접 구현한 기능, 재현 가능한 실행 결과와 문제 해결 기록입니다. "
                    "그 결과를 코드 저장소와 포트폴리오에 남길 때 실무 역량을 보여줄 수 있습니다.")
        return (f"‘{topic}’은 학과의 공동 활동을 기록한 사례입니다. 행사에서 실제로 맡았던 운영·발표·협업 역할이 있다면 "
                "취업 자기소개서의 팀워크와 의사소통 사례로 정리할 수 있습니다. 개발 역량을 직접 증명하는 성과와는 구분하고, "
                "관련 직무 포트폴리오는 본인이 구현한 소프트웨어 프로젝트를 중심으로 준비하는 것이 좋습니다.")
    if category=="학과 소식":
        return (f"‘{topic}’에서 소개된 학과의 교육·실습 방향을 취업 준비로 연결하려면 {roles} 직무에 맞는 프로젝트 경험이 필요합니다. "
                "수업에서 구현한 기능과 데이터·코드·테스트 결과를 정리하고 사용 기술을 채용 공고와 대조해 부족한 부분을 보완하면 "
                "학과 교육 내용을 실질적인 포트폴리오로 바꿀 수 있습니다.")
    if category in ("과거 기록","기술·참고자료"):
        return (f"‘{topic}’은 당시 활동이나 기술 흐름을 살펴볼 수 있는 기록입니다. 현재 채용 요건이나 기술 수준을 그대로 반영하는 자료는 아니므로, "
                f"관련 {roles} 직무를 준비한다면 최신 도구와 요구 역량을 따로 확인하고 실제 구현한 과제를 포트폴리오에 담아야 합니다.")
    return None

def correct_subject_particle(content: str, title: str) -> str:
    # A quoted activity title ending in a vowel takes 는, not 은.
    # Avoid unnatural phrasing such as '논문지 게재’은.
    term="‘"+topic_from_title(title)+"’"
    letters=re.findall(r'[가-힣]',topic_from_title(title))
    if not letters:
        particle="는"
    else:
        particle="은" if (ord(letters[-1])-0xAC00)%28 else "는"
    return content.replace(term+"은",term+particle)


def main() -> None:
    index=INDEX.read_text(encoding="utf-8")
    cards={}
    for m in CARDS.finditer(index):
        entry=m.group(1)
        slug=re.search(r'<h3><a href="/activities/([^/]+)/"',entry)
        name=re.search(r'<h3><a [^>]+>(.*?)</a></h3>',entry,re.S)
        category=re.search(r'<div class="activity-card-meta"><span>(.*?)</span>',entry,re.S)
        lead=re.search(r'</h3><p>(.*?)</p>',entry,re.S)
        if not all((slug,name,category,lead)):
            raise ValueError("Broken index activity")
        cards[slug.group(1)]=(
            clean_text(name.group(1)),clean_text(category.group(1)),clean_text(lead.group(1)))
    if len(cards)!=286:
        raise AssertionError(f"Archive expected 286 posts, got {len(cards)}")
    stats=Counter()
    articles=[]
    new_contexts={}
    previous_contexts=[]
    for slug,(title,category,lead) in cards.items():
        path=ROOT/"activities"/slug/"index.html"
        page=path.read_text(encoding="utf-8")
        # Only treat actual article narrative as evidence, excluding previous
        # generic career advice and general technology explanation.
        narrative=re.search(r'<div class="activity-content">(.*?)<div class="activity-cta">',page,re.S)
        if not narrative:
            raise ValueError("Missing article body: "+slug)
        core=CONTEXT.sub("",narrative.group(1))
        core=re.sub(r'<section class="activity-editorial-explainer">.*?</section>',"",core,flags=re.S)
        original=clean_text(core)
        found=CONTEXT.findall(page)
        if len(found)>1:
            raise ValueError("Duplicated career section "+slug)
        if not found:
            stats['unrelated_or_very_thin_without_context']+=1
            continue
        content=generate_career_text(slug,title,category,original,lead)
        if content:
            content=correct_subject_particle(content,title)
        if not content or len(content)<95:
            raise ValueError(f"Career editorial absent/too short {slug}")
        if "도움이 됩니다" in content or "이해하는 데" in content:
            raise AssertionError("Vague filler "+slug)
        if re.search(r"(?:취업|채용)\s*(?:100%\s*)?보장|전원\s*취업|무조건\s*취업", content):
            if not re.search(r"보장.{0,16}(?:않|아니|없)", content):
                raise AssertionError("Unqualified hiring guarantee "+slug)
        if content in new_contexts.values():
            raise AssertionError("Duplicate career paragraph "+slug)
        new_contexts[slug]=content
        prev=clean_text(found[0])
        previous_contexts.append(prev)
        section=('<section class="activity-editorial-context"><h2>전공과 진로의 연결</h2>'
                 '<p>'+html.escape(content,quote=True)+'</p></section>')
        updated=CONTEXT.sub(lambda m:section,page,count=1)
        if re.findall(r'\bsrc="([^"]+)"',page)!=re.findall(r'\bsrc="([^"]+)"',updated):
            raise AssertionError("Changed image "+slug)
        if re.findall(r'\bhref="([^"]+)"',page)!=re.findall(r'\bhref="([^"]+)"',updated):
            raise AssertionError("Changed link "+slug)
        if updated!=page:
            path.write_text(updated,encoding="utf-8")
            stats['edited']+=1
        stats[category]+=1
        articles.append({"slug":slug,"category":category,"title":title,
                         "before":prev,"after":content,"length":len(content),
                         "hand_edited":slug in HAND_EDITED})
    if not 245 <= len(new_contexts) <= 286:
        raise AssertionError(f"Unanticipated career context count: {len(new_contexts)}")
    stats["hand_edited"]=sum(1 for x in articles if x["hand_edited"])
    stats["distinct_old_paragraphs"]=len(set(previous_contexts))
    stats["distinct_new_paragraphs"]=len(set(new_contexts.values()))
    DETAIL.parent.mkdir(parents=True,exist_ok=True)
    DETAIL.write_text(json.dumps({"date":"2026-10-25","posts":286,
                                  "stats":dict(stats),"articles":articles},
                                  ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary=[
       "# 학과 활동 286건 취업·포트폴리오 연계 문구 전수 교정",
       "",
       "## 편집 원칙",
       "- 수상·프로젝트: 대외 수상 증빙과 실무 개발 포트폴리오, 채용·기술면접에서 활용할 지점을 설명",
       "- 현직자 특강: 채용 직무, 프로젝트 담당 역할, 자기소개서·면접 준비와 연결",
       "- 졸업생 멘토링: 실제 선배의 진로 경로를 참고하되 기업 채용을 보장하지 않음",
       "- 연수·진로체험·학과 행사: 참가자 실적을 학생 개인 취업으로 오인하지 않음",
       "- 사업·산학협력: 협약, 환경 개선 자체가 채용 성과가 아니며 프로젝트 결과물과 구분",
       "- 사진·링크·기존 행사 날짜·제목은 유지",
       "",
       "## 편집량",
       f"- 확인된 게시글: {len(cards)}건",
       f"- 기존 공통 문구 교체: {stats['edited']}건",
       f"- 기존 문구 종류: {stats['distinct_old_paragraphs']}개",
       f"- 교체 후 고유 문구: {stats['distinct_new_paragraphs']}개",
       f"- 대표 성과·특강 기사 수작업 지정: {stats['hand_edited']}건",
       f"- 원문이 너무 짧거나 연계가 부자연스러워 기존에 취업 문구가 없던 기사: {stats['unrelated_or_very_thin_without_context']}건",
       "",
       "## 게시글별 반영 문구",
       "",
    ]
    for item in articles:
        summary += [
           f"### [{item['title']}](https://ai.k-bigdata.kr/activities/{item['slug']}/)",
           f"- 분류: {item['category']}",
           f"- 변경 문구: {item['after']}",
           "",
        ]
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text("\n".join(summary),encoding="utf-8")
    print("CAREER_CONTEXT_EDITORIAL_AUDIT",json.dumps(dict(stats),ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
