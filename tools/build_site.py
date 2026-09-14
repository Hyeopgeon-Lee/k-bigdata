#!/usr/bin/env python3
"""Build a crawlable static department site from data/posts.json."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import date, datetime, time, timedelta, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path
from string import Template
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
POSTS_FILE = ROOT / "data" / "posts.json"
TEMPLATE_FILE = ROOT / "tools" / "templates" / "insight.html"
ARCHIVE_TEMPLATE_FILE = ROOT / "tools" / "templates" / "insights-index.html"
SITE_URL = "https://ai.k-bigdata.kr"
DEPARTMENT = "한국폴리텍대학 서울강서캠퍼스 빅데이터소프트웨어공학과"
SOCIAL_IMAGE = f"{SITE_URL}/assets/promo/og-share-2027-susi1.png"
KST = timezone(timedelta(hours=9))
EXCLUDED = {".git", ".github", ".idea", "_site", "tools"}
STATIC_PAGES = (
    ("", "index.html"),
    ("ai-software/", "ai-software/index.html"),
    ("data-analysis/", "data-analysis/index.html"),
    ("backend-software/", "backend-software/index.html"),
    ("seoul-it-college/", "seoul-it-college/index.html"),
    ("career-portfolio/", "career-portfolio/index.html"),
    ("privacy.html", "privacy.html"),
)


def html(value: object) -> str:
    return escape(str(value or ""), quote=True)


def load_posts() -> list[dict]:
    posts = json.loads(POSTS_FILE.read_text(encoding="utf-8"))
    required = {"slug", "date", "title", "excerpt", "source", "sourceUrl", "connection"}
    seen: set[str] = set()
    for post in posts:
        missing = sorted(required.difference(post))
        if missing:
            raise ValueError(f"{post.get('slug', 'unknown')}: missing {', '.join(missing)}")
        if post["slug"] in seen:
            raise ValueError(f"Duplicate slug: {post['slug']}")
        seen.add(post["slug"])
        datetime.strptime(post["date"], "%Y-%m-%d")
    return sorted(posts, key=lambda item: (item["date"], item["slug"]), reverse=True)


def copy_public_files() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    for item in ROOT.iterdir():
        if item.name in EXCLUDED or item.name in {"README.md", ".gitignore", "sitemap.xml"}:
            continue
        target = OUTPUT / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def post_url(post: dict) -> str:
    return f"{SITE_URL}/insights/{post['slug']}/"


def compact_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def learning_context(post: dict) -> tuple[list[str], str]:
    tag = post.get("tag", "").upper()
    if "입학" in tag:
        return (
            ["공식 모집요강에서 지원 자격과 일정을 확인하기", "교과목 이름보다 공개된 학생 프로젝트를 비교하기", "상담을 통해 기초부터 포트폴리오까지의 학습 흐름 확인하기"],
            "지원 전에는 공식 모집요강과 학생 결과물을 함께 살펴보고, 자신의 관심 분야가 AI·데이터·백엔드·클라우드 가운데 어디와 연결되는지 질문해 보세요.",
        )
    if "DATA" in tag:
        return (
            ["분석에 필요한 데이터의 출처와 품질 확인하기", "SQL·Python으로 재현 가능한 분석 과정 설계하기", "결과를 시각화와 소프트웨어 기능으로 전달하기"],
            "이 이슈를 수업 프로젝트로 확장한다면 공개데이터를 수집·정제하고, 분석 결과를 사용자가 탐색할 수 있는 작은 서비스로 구현해 볼 수 있습니다.",
        )
    if "CLOUD" in tag or "SW" in tag:
        return (
            ["사용자 요구사항을 API와 데이터 구조로 나누기", "배포·확장·장애 대응 조건까지 함께 설계하기", "코드·테스트·운영 기록을 포트폴리오로 남기기"],
            "이 이슈를 수업 프로젝트로 확장한다면 핵심 기능을 API로 구현하고, 컨테이너와 클라우드 환경에서 배포·관측하는 과정까지 검증해 볼 수 있습니다.",
        )
    return (
        ["기사의 주장과 원문 근거를 구분해 확인하기", "AI 기능에 필요한 데이터와 평가 기준 정의하기", "모델 결과를 API·화면·클라우드 운영으로 연결하기"],
        "이 이슈를 수업 프로젝트로 확장한다면 해결할 문제와 평가 기준을 먼저 정하고, 데이터 준비부터 AI 기능·백엔드 API·사용자 화면까지 작은 프로토타입으로 검증해 볼 수 있습니다.",
    )


def render_related(posts: list[dict], current: dict) -> str:
    related = [post for post in posts if post["slug"] != current["slug"] and post.get("tag") == current.get("tag")]
    if len(related) < 3:
        selected = {post["slug"] for post in related}
        related.extend(
            post for post in posts
            if post["slug"] != current["slug"] and post["slug"] not in selected
        )
    items = []
    for post in related[:3]:
        items.append(
            f'<li><a href="/insights/{html(post["slug"])}/">'
            f'<time datetime="{html(post["date"])}">{html(post["date"].replace("-", "."))}</time>'
            f'<strong>{html(post["title"])}</strong></a></li>'
        )
    return "".join(items)


def render_post(template: Template, posts: list[dict], post: dict) -> str:
    url = post_url(post)
    source_prefix = f"{post['source']}이(가)"
    source_credit = f"출처 ‘{post['source']}’는"
    paragraphs = [
        str(paragraph).replace(source_prefix, source_credit)
        for paragraph in post.get("body", [post["excerpt"]])
        if str(paragraph).strip() != str(post["connection"]).strip()
    ]
    body = "".join(f"<p>{html(paragraph)}</p>" for paragraph in paragraphs)
    learning_points, project_prompt = learning_context(post)
    editorial_note = ""
    if post.get("automated"):
        editorial_note = (
            '<aside class="editorial-note"><strong>자동 발행 안내</strong>'
            '<p>이 글은 공개된 기사 제목과 출처를 바탕으로 자동 구성한 학과 홍보용 기술 인사이트입니다. '
            '원문의 세부 내용과 수치는 연결된 출처에서 직접 확인해 주세요.</p></aside>'
        )
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "description": post["excerpt"],
        "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "datePublished": f"{post['date']}T06:00:00+09:00",
        "dateModified": f"{post.get('lastModified', post['date'])}T06:00:00+09:00",
        "image": SOCIAL_IMAGE,
        "inLanguage": "ko-KR",
        "isBasedOn": post["sourceUrl"],
        "author": {
            "@type": "Organization",
            "name": "빅데이터소프트웨어공학과",
            "url": f"{SITE_URL}/",
            "parentOrganization": {
                "@type": "CollegeOrUniversity",
                "name": "한국폴리텍대학 서울강서캠퍼스",
            },
        },
        "publisher": {
            "@type": "EducationalOrganization",
            "name": DEPARTMENT,
            "url": f"{SITE_URL}/",
        },
    }
    return template.safe_substitute(
        title=html(post["title"]),
        description=html(post["excerpt"]),
        canonical_url=html(url),
        tag=html(post.get("tag", "AI · IT INSIGHT")),
        date_iso=html(post["date"]),
        date_display=html(post["date"].replace("-", ".")),
        source=html(post["source"]),
        source_url=html(post["sourceUrl"]),
        body=body,
        connection=html(post["connection"]),
        learning_points="".join(f"<li>{html(point)}</li>" for point in learning_points),
        project_prompt=html(project_prompt),
        editorial_note=editorial_note,
        related=render_related(posts, post),
        schema=compact_json(schema),
        social_image=SOCIAL_IMAGE,
    )


def render_story_cards(posts: list[dict], limit: int | None = 6) -> str:
    cards = []
    selected = posts if limit is None else posts[:limit]
    for post in selected:
        cards.append(
            '<article class="story-card">'
            '<div class="story-meta">'
            f'<span class="story-tag">{html(post.get("tag", "AI · IT"))}</span>'
            f'<time datetime="{html(post["date"])}">{html(post["date"].replace("-", "."))}</time>'
            '</div>'
            f'<h3>{html(post["title"])}</h3>'
            f'<p>{html(post["excerpt"])}</p>'
            f'<a href="/insights/{html(post["slug"])}/" aria-label="{html(post["title"])} 자세히 읽기">'
            '인사이트 읽기 <span aria-hidden="true">→</span></a>'
            '</article>'
        )
    return "\n            ".join(cards)


def update_home(posts: list[dict]) -> None:
    home_file = OUTPUT / "index.html"
    home = home_file.read_text(encoding="utf-8")
    pattern = re.compile(r"(<!-- GENERATED_STORIES_START -->).*?(<!-- GENERATED_STORIES_END -->)", re.DOTALL)
    home, count = pattern.subn(
        lambda match: f"{match.group(1)}\n            {render_story_cards(posts)}\n            {match.group(2)}",
        home,
    )
    if count != 1:
        raise ValueError("Homepage story marker was not found exactly once")
    home_file.write_text(home, encoding="utf-8")


def write_archive(posts: list[dict]) -> None:
    template = Template(ARCHIVE_TEMPLATE_FILE.read_text(encoding="utf-8"))
    latest_date = posts[0]["date"] if posts else date.today().isoformat()
    archive = template.safe_substitute(cards=render_story_cards(posts, limit=None), latest_date=latest_date)
    target = OUTPUT / "insights" / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(archive, encoding="utf-8")


def git_last_modified(path: str) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", path],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return result[:10] if result else date.today().isoformat()
    except (OSError, subprocess.CalledProcessError):
        return date.today().isoformat()


def write_sitemap(posts: list[dict]) -> None:
    urls = [
        (f"{SITE_URL}/{relative_url}", git_last_modified(source_path))
        for relative_url, source_path in STATIC_PAGES
    ]
    if posts:
        urls.append((f"{SITE_URL}/insights/", posts[0]["date"]))
    urls.extend((post_url(post), post.get("lastModified", post["date"])) for post in posts)
    entries = "\n".join(
        "  <url>\n"
        f"    <loc>{xml_escape(url)}</loc>\n"
        f"    <lastmod>{xml_escape(modified)}</lastmod>\n"
        "  </url>"
        for url, modified in urls
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )
    (OUTPUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def write_feed(posts: list[dict]) -> None:
    items = []
    for post in posts[:20]:
        published = datetime.combine(datetime.strptime(post["date"], "%Y-%m-%d").date(), time(6), tzinfo=KST)
        url = post_url(post)
        items.append(
            "    <item>\n"
            f"      <title>{xml_escape(post['title'])}</title>\n"
            f"      <link>{xml_escape(url)}</link>\n"
            f"      <guid isPermaLink=\"true\">{xml_escape(url)}</guid>\n"
            f"      <pubDate>{format_datetime(published)}</pubDate>\n"
            f"      <description>{xml_escape(post['excerpt'])}</description>\n"
            "    </item>\n"
        )
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        "    <title>빅데이터소프트웨어공학과 AI·IT 인사이트</title>\n"
        f"    <link>{SITE_URL}/</link>\n"
        "    <description>AI·데이터·클라우드 기술 흐름을 학과 교육과 진로 관점에서 소개합니다.</description>\n"
        "    <language>ko-KR</language>\n"
        + "".join(items)
        + "  </channel>\n"
        "</rss>\n"
    )
    (OUTPUT / "feed.xml").write_text(feed, encoding="utf-8")


def main() -> None:
    posts = load_posts()
    template = Template(TEMPLATE_FILE.read_text(encoding="utf-8"))
    copy_public_files()
    for post in posts:
        target = OUTPUT / "insights" / post["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_post(template, posts, post), encoding="utf-8")
    update_home(posts)
    write_archive(posts)
    write_sitemap(posts)
    write_feed(posts)
    print(f"Built {len(posts)} insight pages in {OUTPUT}")


if __name__ == "__main__":
    main()
