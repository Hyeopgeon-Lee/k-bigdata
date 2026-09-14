#!/usr/bin/env python3
"""Fetch a recent Korean AI/IT headline and publish a grounded department post."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
POSTS_FILE = ROOT / "data" / "posts.json"
KST = timezone(timedelta(hours=9))
SEARCHES = (
    "인공지능 AI 데이터 산업 기술",
    "AI 에이전트 클라우드 소프트웨어 개발",
    "빅데이터 데이터분석 개발자 취업",
)
KEYWORDS = {
    "AI · AGENT": ("에이전트", "생성형", "LLM", "인공지능", "AI"),
    "DATA": ("빅데이터", "데이터", "분석", "통계"),
    "CLOUD · SW": ("클라우드", "소프트웨어", "개발자", "DevOps", "플랫폼"),
}
SCHOOL_TERMS = ("대학교", "대학", "캠퍼스", "학교", "학생", "교수", "연구팀", "연구진")
SCHOOL_NAME_PATTERN = re.compile(r"[가-힣]{2,}대(?:\s|,|·|…|SW|AI|연구|학생|교수)")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


def is_school_story(title: str) -> bool:
    lowered = title.lower()
    return any(term.lower() in lowered for term in SCHOOL_TERMS) or bool(SCHOOL_NAME_PATTERN.search(title))


def source_name(title: str, source: str) -> str:
    if source:
        return clean(source)
    match = re.search(r"\s+-\s+([^\-]+)$", title)
    return clean(match.group(1)) if match else "Google 뉴스"


def choose_tag(title: str) -> str:
    for tag, words in KEYWORDS.items():
        if any(word.lower() in title.lower() for word in words):
            return tag
    return "AI · IT"


def connection_for(title: str) -> str:
    lowered = title.lower()
    if any(word in lowered for word in ("에이전트", "생성형", "llm", "인공지능", "ai")):
        return "빅데이터소프트웨어공학과에서는 Python과 자연어처리, AI 프로그래밍을 소프트웨어 프로젝트와 연결합니다. 도구를 사용하는 데서 멈추지 않고, 데이터와 AI를 실제 서비스로 구현하는 역량을 기릅니다."
    if any(word in lowered for word in ("클라우드", "devops", "플랫폼", "소프트웨어")):
        return "학과의 Java 백엔드, MSA, K-PaaS, 클라우드·DevOps 학습은 AI 기능을 안정적인 서비스로 운영하는 기반이 됩니다. 구현부터 배포까지 경험한 프로젝트가 취업 포트폴리오로 이어집니다."
    return "학과에서는 Python·R·SQL로 데이터를 수집하고 분석한 뒤, 결과를 AI와 소프트웨어 서비스로 확장합니다. 최신 산업 이슈를 프로젝트 주제로 바꾸는 경험이 실무형 문제해결력을 만듭니다."


def content_for(title: str, source: str) -> dict:
    lowered = title.lower()
    if any(word in lowered for word in ("피지컬", "로봇", "비전", "영상", "센서", "자율")):
        excerpt = "현실을 인식하는 AI 기술을 데이터 수집, 컴퓨터비전, 실시간 처리와 안전한 소프트웨어 설계 관점에서 살펴봅니다."
        focus_heading = "현실의 데이터는 실험실 데이터보다 복잡합니다"
        focus_paragraphs = [
            "카메라와 센서 데이터에는 조명, 각도, 가림, 움직임과 장치 오차가 함께 들어옵니다. 모델을 선택하기 전에 어떤 환경에서 어떤 데이터를 수집하고, 오탐과 미탐을 어떻게 확인할지 정의해야 합니다.",
            "정확도만큼 처리속도와 안전한 예외 처리도 중요합니다. AI가 판단하기 어려운 상황을 감지하고 사용자 확인이나 대체 동작으로 연결하는 소프트웨어 구조가 필요합니다.",
        ]
        learning = ["센서 데이터의 수집 조건과 품질 기록하기", "정확도·오탐·미탐·처리속도를 함께 측정하기", "AI 추론 결과를 API와 사용자 화면에 연결하기"]
        project = "안전한 이미지 분류 주제를 정해 데이터 수집부터 OpenCV 전처리, AI 추론과 웹 대시보드까지 작은 서비스로 구현해 보세요."
    elif any(word in lowered for word in ("클라우드", "배포", "플랫폼", "인프라", "cpu", "gpu", "데이터센터")):
        excerpt = "AI 기능을 실제 서비스로 운영하기 위해 필요한 백엔드, 클라우드, 성능·비용 측정과 장애 대응 역량을 살펴봅니다."
        focus_heading = "AI 모델 밖의 소프트웨어가 서비스 품질을 결정합니다"
        focus_paragraphs = [
            "AI 서비스에는 모델 호출뿐 아니라 데이터베이스, API, 인증, 캐시와 사용자 화면이 필요합니다. 각 구성요소가 실패할 수 있으므로 시간 제한, 재시도와 대체 응답을 설계해야 합니다.",
            "배포 뒤에는 요청 수, 응답시간, 오류율, 서버 자원과 모델 사용 비용을 관찰해야 합니다. 측정 결과를 바탕으로 병목을 찾고 자동 테스트와 배포 과정에서 다시 검증하는 습관이 중요합니다.",
        ]
        learning = ["서비스를 데이터·모델·API·화면으로 나누어 설계하기", "응답시간·오류율·비용의 목표값 정하기", "로그와 자동 배포 기록을 포트폴리오에 남기기"]
        project = "AI 문서 검색 API를 컨테이너로 배포하고, 요청 수와 응답시간을 기록하는 모니터링 화면까지 만들어 보세요."
    elif any(word in lowered for word in ("데이터", "분석", "품질", "예측", "추천")):
        excerpt = "최신 데이터·AI 흐름을 문제 정의, 데이터 품질, 재현 가능한 분석과 소프트웨어 서비스 구현 관점에서 살펴봅니다."
        focus_heading = "좋은 분석은 도구보다 질문과 데이터에서 시작됩니다"
        focus_paragraphs = [
            "먼저 누가 어떤 문제를 겪고 있으며 데이터로 어떤 판단을 도울 것인지 정해야 합니다. 질문이 구체적일수록 필요한 데이터와 평가 기준도 분명해집니다.",
            "데이터의 출처와 갱신일, 누락과 중복 처리 과정을 기록하고 분석 코드를 재현 가능하게 남겨야 결과를 믿을 수 있습니다. 분석 결과를 API와 화면에 연결하면 사용자가 행동할 수 있는 서비스가 됩니다.",
        ]
        learning = ["사용자와 해결할 문제를 한 문장으로 정의하기", "데이터 출처·품질·정제 규칙 기록하기", "분석 결과를 API와 시각화 기능으로 전달하기"]
        project = "공공데이터에서 생활 문제 하나를 정해 데이터 명세서, 정제 코드, 분석 결과와 웹 서비스를 한 저장소에 정리해 보세요."
    else:
        excerpt = "최신 AI 흐름을 데이터, 도구 연결, 품질 평가, 백엔드와 클라우드 운영 관점에서 살펴봅니다."
        focus_heading = "AI 에이전트는 모델이 아니라 전체 실행 구조입니다"
        focus_paragraphs = [
            "AI 에이전트는 목표를 해석하고 필요한 정보를 찾으며 여러 도구를 순서대로 호출합니다. 개발자는 접근 가능한 데이터와 권한, 작업 실패 시 재시도 조건과 사용자에게 결과를 설명할 방법을 함께 설계해야 합니다.",
            "품질은 느낌이 아니라 평가 질문, 근거 일치율, 업무 완료율과 도구 호출 성공률로 측정해야 합니다. 응답시간과 비용까지 기록하면 실제 사용 가능한 서비스로 개선할 수 있습니다.",
        ]
        learning = ["에이전트의 목표와 성공 기준 정의하기", "데이터·도구·권한과 실패 대응 설계하기", "정확도·응답시간·비용을 반복 측정하기"]
        project = "공식 문서를 검색하고 근거 링크를 제시하는 안내 에이전트를 구현한 뒤, 평가 질문과 오류 개선 기록을 남겨 보세요."

    return {
        "excerpt": excerpt,
        "learningPoints": learning,
        "projectPrompt": project,
        "sections": [
            {
                "heading": "이 기술 소식에서 읽어야 할 변화",
                "paragraphs": [
                    f"출처 ‘{source}’는 ‘{title}’ 소식을 전했습니다. 이 글은 기사에 없는 내용을 추측하지 않고, 제목으로 확인되는 기술 흐름을 학생의 학습과 프로젝트 관점에서 해석합니다.",
                    "기술 이름을 외우는 것보다 어떤 문제를 해결하고, 필요한 데이터를 어떻게 준비하며, 결과를 작동하는 소프트웨어로 어떻게 연결할지 이해하는 것이 중요합니다.",
                ],
            },
            {"heading": focus_heading, "paragraphs": focus_paragraphs},
            {
                "heading": "학과 프로젝트와 취업 포트폴리오로 연결하는 방법",
                "paragraphs": [
                    "프로젝트에는 완성 화면만 남기지 말고 문제 정의, 데이터 출처, 시스템 구조도, 담당 역할, 테스트와 개선 과정을 함께 기록해야 합니다. 실패 원인과 해결 과정을 설명할 수 있을 때 실제 개발 역량이 드러납니다.",
                    "빅데이터소프트웨어공학과에서는 Python·Java·SQL의 기초에서 시작해 AI, 백엔드 API와 클라우드 배포까지 연결합니다. 최신 기술 흐름을 작은 서비스로 구현하는 경험이 진로를 구체화하는 포트폴리오가 됩니다.",
                ],
            },
        ],
    }


def fetch_candidates() -> list[dict]:
    candidates: list[dict] = []
    for query in SEARCHES:
        url = f"https://news.google.com/rss/search?q={quote(query + ' when:7d')}&hl=ko&gl=KR&ceid=KR:ko"
        request = Request(url, headers={"User-Agent": "K-BigData-Department-News/1.0"})
        with urlopen(request, timeout=20) as response:
            root = ElementTree.fromstring(response.read())
        for item in root.findall(".//item"):
            title = clean(item.findtext("title", ""))
            link = clean(item.findtext("link", ""))
            published_raw = item.findtext("pubDate", "")
            source_node = item.find("source")
            source = clean(source_node.text if source_node is not None and source_node.text else "")
            if not title or not link or not link.startswith("https://news.google.com/"):
                continue
            if is_school_story(title):
                continue
            try:
                published = parsedate_to_datetime(published_raw)
            except (TypeError, ValueError):
                published = datetime.now(timezone.utc)
            score = sum(3 for words in KEYWORDS.values() for word in words if word.lower() in title.lower())
            age = max(0, (datetime.now(timezone.utc) - published.astimezone(timezone.utc)).days)
            candidates.append({
                "title": re.sub(r"\s+-\s+[^-]+$", "", title).strip(),
                "link": link,
                "source": source_name(title, source),
                "published": published,
                "score": score + max(0, 7 - age),
            })
    candidates.sort(key=lambda item: (item["score"], item["published"]), reverse=True)
    return candidates


def slugify(title: str, date: str) -> str:
    ascii_bits = re.findall(r"[a-z0-9]+", title.lower())[:5]
    suffix = "-".join(ascii_bits) or f"insight-{sum(map(ord, title))}"
    return f"{date}-{suffix}"


def main() -> int:
    posts = json.loads(POSTS_FILE.read_text(encoding="utf-8"))
    known_urls = {post.get("sourceUrl") for post in posts}
    known_titles = {post.get("title") for post in posts}
    try:
        candidate = next(item for item in fetch_candidates() if item["link"] not in known_urls and item["title"] not in known_titles)
    except (StopIteration, OSError, ElementTree.ParseError) as exc:
        print(f"No new trustworthy headline was available: {exc}")
        return 0

    today = datetime.now(KST).date().isoformat()
    title = candidate["title"]
    content = content_for(title, candidate["source"])
    post = {
        "slug": slugify(title, today),
        "date": today,
        "tag": choose_tag(title),
        "title": title,
        "excerpt": content["excerpt"],
        "source": candidate["source"],
        "sourceUrl": candidate["link"],
        "connection": connection_for(title),
        "automated": True,
        "learningPoints": content["learningPoints"],
        "projectPrompt": content["projectPrompt"],
        "sections": content["sections"],
    }
    posts.insert(0, post)
    POSTS_FILE.write_text(json.dumps(posts[:30], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Published: {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
