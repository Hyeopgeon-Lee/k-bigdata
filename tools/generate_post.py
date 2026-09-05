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


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


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
    post = {
        "slug": slugify(title, today),
        "date": today,
        "tag": choose_tag(title),
        "title": title,
        "excerpt": f"{candidate['source']}의 최신 보도를 학과 교육과 진로 관점에서 읽어봅니다.",
        "source": candidate["source"],
        "sourceUrl": candidate["link"],
        "connection": connection_for(title),
        "body": [
            f"{candidate['source']}이(가) 최근 ‘{title}’ 소식을 전했습니다. 이 글은 기사 제목과 공개된 출처를 바탕으로 기술 흐름이 학생의 학습과 진로에 주는 의미를 살펴봅니다.",
            "빠르게 바뀌는 IT 산업에서는 한 가지 도구를 외우는 것보다 데이터를 이해하고, 문제를 정의하고, 작동하는 소프트웨어로 구현하는 기초 체력이 중요합니다. 새로운 기술이 등장해도 프로그래밍·데이터베이스·클라우드의 원리를 아는 사람은 변화에 더 빠르게 적응할 수 있습니다.",
            connection_for(title),
            "원문의 세부 내용과 수치는 아래 출처 링크에서 직접 확인할 수 있습니다. 학과에서는 최신 기술 이슈를 수업과 프로젝트 주제로 연결해 학생이 스스로 검증하고 구현하는 경험을 쌓도록 돕습니다.",
        ],
    }
    posts.insert(0, post)
    POSTS_FILE.write_text(json.dumps(posts[:30], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Published: {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
