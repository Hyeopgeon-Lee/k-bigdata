#!/usr/bin/env python3
"""Enforce student-led-only career context on published department activities.

A section about '전공과 진로의 연결' is appropriate only when the source
documents a student-initiated or student-performed action (not an instructor
lecture, faculty research, technology consulting, official visit or training
provided to outsiders). Conservative by design; uncertainty means no section.
"""
from __future__ import annotations
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "activities/index.html"
REPORT = ROOT / "reports/student_led_career_policy.json"
REMOVED = {"kopo-591399", "kopo-591393"}
CARD = re.compile(r'<article class="activity-card">.*?</article>', re.S)
CAREER = re.compile(
    r'<section class="activity-editorial-context">\s*'
    r'<h2>전공과 진로의 연결</h2>.*?</section>\s*', re.S
)
DENIED = {"교원 연수", "전문가 특강", "산학협력", "지역사회 교육",
          "학과 소식", "과거 기록", "기술·참고자료"}
PROFESSIONAL = re.compile(r'교수|교원|교사|학과장|국회의원|공무원|의원|강사|이사|박사')
STUDENT = re.compile(r'재학생|학과 학생|학생 팀|학생들|학생들이|[12]학년|동아리|졸업작품')
ACTION = re.compile(
    r'학생.{0,95}(?:수상|개발|구현|출품|운영|진행|참가|참여|발표|제작|'
    r'선정|전시|제출|봉사|기획)|'
    r'(?:[12]학년|동아리).{0,95}(?:수상|개발|구현|출품|운영|'
    r'참가|참여|발표|제작|선정|전시|멘토링|지도)'
)
# Source-confirmed cases in which students actively implemented, participated,
# ran booths or taught their peers. No faculty-only consulting is included.
STUDENT_EVIDENCE = {
    "sesac-hackathon-grand-prize-2025", "gangseo-job-fair-2026",
    "kopo-775378", "kopo-775379", "kopo-762210",
    "kopo-750981", "kopo-750066", "kopo-699006",
    "kopo-758194", "kopo-749927",
}
SPORT = re.compile(r'운동회|풋살|피구|줄다리기|산책|체육|다과회|축제')
NON_STUDENT = re.compile(r'참여학과 선정|초청 특강|현직자 특강|기술지도|기술 자문|'
                         r'교수진|교원 대상|교사 대상|연수|사업 설명회')
OUTSIDER_EDUCATION = re.compile(
    r'고교생 대상|고등학생 대상|중학생.*?(?:대상|직업체험)|'
    r'고교 대상|고교생.*?교육|고교생.*?체험|'
    r'여고 학생 대상|경복여고 학생 대상'
)
CAREER_FAIR = re.compile(r'취업박람회|일자리박람회|채용박람회')
PROJECT = re.compile(r'졸업작품|프로젝트 (?:개발|전시|발표)|'
                     r'경진대회|해커톤|한이음|소프트웨어.*?공모전')

def strip(source: str) -> str:
    return " ".join(html.unescape(re.sub(r'<[^>]+>', " ", source)).split())

def is_student_led(slug: str, category: str, title: str,
                   summary: str, original: str) -> bool:
    """Require affirmative evidence of student action; never infer from school hosting."""
    if slug in REMOVED or category in DENIED:
        return False
    if slug in STUDENT_EVIDENCE:
        return True
    context = f"{title} {summary} {original[:1400]}"
    if SPORT.search(title) or OUTSIDER_EDUCATION.search(title):
        return False
    if NON_STUDENT.search(title) and not (category == "학생 프로젝트" and STUDENT.search(context)):
        return False
    if category == "멘토링·진로":
        return bool(re.search(r'선후배|2학년 선배|학생.*?멘토|학년.*?멘토|재학생.*?지도', title + ' ' + summary)) and not bool(re.search(r'졸업생|현직자|초청', title))
    if category == "학생 프로젝트":
        return bool(PROJECT.search(title) or STUDENT.search(title)) and "참여학과 선정" not in title
    if category in {"수상·성과", "연구·학술"}:
        if PROFESSIONAL.search(title) and not STUDENT.search(title):
            return False
        return bool(STUDENT.search(context) and (ACTION.search(context) or (STUDENT.search(title) and re.search(r'수상|발표|공모전',title))))
    if category == "취업·진로":
        return bool(CAREER_FAIR.search(title) and STUDENT.search(context) and ACTION.search(context))
    if category == "진로체험":
        # Career fair organizers, not secondary-school attendees.
        return bool(re.search(r'재학생.{0,95}(?:운영|진행)|학생들.{0,95}(?:부스 운영|체험 진행)', original))
    if category == "학과 행사":
        return bool(PROJECT.search(title) and STUDENT.search(context) and ACTION.search(context))
    if category == "사회공헌·봉사":
        return bool(re.search(r'컴퓨터 유지보수|재능기부|SW동아리|기술봉사', title+' '+original) and STUDENT.search(context) and ACTION.search(context))
    return False

def main() -> None:
    archive = INDEX.read_text(encoding="utf-8")
    cards = CARD.findall(archive)
    if len(cards) != 284:
        raise ValueError(f"Expected 284 visible records after removing cardnews; got {len(cards)}")
    changes, allowed, excluded = [], [], []
    for item in cards:
        match = re.search(r'<h3><a href="/activities/([^/]+)/"', item)
        if not match:
            raise ValueError("Malformed card")
        slug = match.group(1)
        category = strip(re.search(r'<div class="activity-card-meta"><span>(.*?)</span>',item,re.S).group(1))
        title = strip(re.search(r'<h3><a[^>]+>(.*?)</a>',item,re.S).group(1))
        summary = strip(re.search(r'</h3><p>(.*?)</p>',item,re.S).group(1))
        path = ROOT / "activities" / slug / "index.html"
        source = path.read_text(encoding="utf-8")
        original = re.search(
            r'<div class="activity-content">(.*?)<div class="activity-cta">',
            source, re.S
        )
        if not original:
            raise ValueError(f"Missing activity body {slug}")
        event = re.split(r'<section class="activity-editorial-', original.group(1))[0]
        keep = is_student_led(slug, category, title, summary, strip(event))
        existing = len(CAREER.findall(source))
        if existing > 1:
            raise ValueError(f"Duplicate career panels: {slug}")
        if keep:
            allowed.append(slug)
        else:
            excluded.append(slug)
            if existing:
                replacement = CAREER.sub("",source)
                path.write_text(replacement,encoding="utf-8")
                changes.append(slug)
    report = {
        "total":len(cards), "policy":"Only source-supported student-led activity may have a career connection.",
        "student_led_eligible":len(allowed), "non_student_or_unverified":len(excluded),
        "sections_removed":len(changes), "removed_from":changes,
        "student_led_slugs":allowed, "excluded_slugs":excluded, "removed_cardnews":sorted(REMOVED)
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:report[key] for key in (
        "total","student_led_eligible","non_student_or_unverified","sections_removed"
    )},ensure_ascii=False))

if __name__ == "__main__":
    main()
