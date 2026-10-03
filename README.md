# 빅데이터소프트웨어공학과 홍보 홈페이지

[![2027학년도 빅데이터소프트웨어공학과 입학안내](https://ai.k-bigdata.kr/assets/promo/og-department.png)](https://ai.k-bigdata.kr/admission/2027/)

<p align="center">
  <a href="https://ai.k-bigdata.kr/admission/2027/"><img src="https://img.shields.io/badge/2027학년도-수시2차·정시%20입학안내-CBFF3D?style=for-the-badge&labelColor=071A33" alt="2027학년도 수시2차·정시 입학안내"></a>
</p>

> 현재 모집 상태와 원서접수·모집요강·상담은 [2027 입학안내](https://ai.k-bigdata.kr/admission/2027/)에서 확인합니다. 종료된 전형을 모집 중으로 안내하지 않습니다.

한국폴리텍대학 서울강서캠퍼스 **빅데이터소프트웨어공학과** 홍보 홈페이지입니다.

- [학과 홈페이지](https://ai.k-bigdata.kr/)
- [졸업생 포트폴리오](https://portfolio.k-bigdata.kr/)
- [교수 기술 블로그](https://prof.k-bigdata.kr/)

## 주요 구성

- 2027학년도 수시2차·정시 일정과 모집 상태별 다음 행동
- AI·빅데이터·소프트웨어·클라우드 교육 로드맵
- 공모전 수상, 취업 진로, 졸업 포트폴리오 안내
- 최신 AI·IT 기사를 학과 교육과 연결한 정기 인사이트
- 검색엔진이 바로 읽을 수 있는 글별 정적 HTML·고유 주소
- 글별 `BlogPosting` 구조화 데이터, 자동 사이트맵과 RSS

## 자동 발행

Codex 예약 작업 **학과 AI·IT 인사이트 심층 발행**이 월·수·금 오전 6시(한국시간)에 공식 원문을 조사하고 깊이 있는 교육용 글을 작성합니다. PC와 Codex가 실행 가능한 상태여야 합니다. 본문 3,000자 이상, 6개 절, 공식 출처 2개 이상, 비교·실습·평가 내용을 검증한 뒤 발행합니다. 자세한 기준은 `tools/INSIGHT_EDITORIAL.md`를 참고하세요.

배포할 때 `tools/build_site.py`가 다음 결과물을 자동 생성합니다.

- `/insights/` 전체 글 목록과 `/insights/글주소/` 형식의 고유 정적 게시글
- 제목·설명·작성 조직·발행일이 포함된 `BlogPosting` 구조화 데이터
- 홈페이지 최신 글 카드와 주제별 관련 글
- 신규 글과 `lastmod`가 포함된 `/sitemap.xml`
- 네이버와 RSS 구독기가 확인할 수 있는 `/feed.xml`

기존 `post.html?slug=...` 주소는 대응하는 새 정적 주소로 자동 이동합니다. 사이트맵과 RSS는 빌드 결과물이므로 저장소에서 직접 수정하지 않습니다.

GitHub Actions는 글 검증과 배포만 담당합니다. 수동 실행은 기존 글을 다시 배포하며 새 글을 만들지 않습니다. 새 글은 `python tools/generate_post.py --input draft.json`으로 검증·추가합니다. 조사와 작성에 필요한 시간에 따라 게시 시각은 오전 6시 이후가 될 수 있습니다.

## 모집 일정 자동 전환

`data/admissions.json`이 일정·모집인원·공식 URL·SEO 문구·상태별 CTA의 단일 원본입니다. `admission.js`의 동일 상태 엔진을 Node로 빌드에서 실행하고, 브라우저에서는 빌드가 삽입한 원본 데이터로 30초마다 화면만 갱신합니다. 메타정보는 브라우저 JavaScript에 의존하지 않습니다.

수시1차 접수 종료 → 수시2차 예정 → 수시2차 접수중 → 정시 예정 → 정시 접수중 → 정규모집 종료 순으로 한국시간에 맞춰 전환합니다. 이전 전형의 면접·발표는 보조 안내로 유지합니다. 접수 전 CTA는 `/admission/2027/`, 접수중에는 온라인 원서접수, 정규모집 종료 후에는 공식 입학안내로 이동합니다. 추가모집 날짜를 추정하지 않습니다.

매일 한국시간 00:37(UTC 15:37)에 GitHub Actions가 검증·정적 빌드·Pages 배포·IndexNow 알림을 실행합니다. 예약 실행은 Git commit을 만들지 않습니다. GitHub의 예약 실행은 지연될 수 있으므로 브라우저 화면의 날짜 전환도 유지합니다. 새 학년도는 공식 발표 후 데이터와 자산을 갱신해야 합니다. 다른 저장소의 admission.js는 이 저장소와 독립되어 있으며 이번 변경을 자동 복제하지 않습니다.

메인과 입학안내의 title·description·OG·Twitter·JSON-LD·Hero·일정·CTA가 정적으로 생성됩니다. 학과 기본/수시2차/정시/인사이트/프로젝트/취업의 1200×630 OG 이미지를 구분합니다. 기존 URL과 검색 소유확인 파일은 보존합니다.

## 공식 정보

- [학과 공식 홈페이지](https://www.kopo.ac.kr/kangseo/content.do?menu=1547)
- [2027학년도 모집요강](https://kopo.ac.kr/kangseo/content.do?menu=321)
- [온라인 원서접수](https://apply.jinhakapply.com/Notice/5041044/A)
- [입학 상담 오픈채팅](https://open.kakao.com/o/gEd0JIad)

> 입학 일정과 전형 기준은 대학 사정에 따라 바뀔 수 있으므로 공식 모집요강을 우선합니다.
# 졸업생 취업현황 연동

`/employment/`은 BigData Alumni Network의 읽기 전용 `careerPublic` API를 이용합니다. 빌드에는 현재 졸업연도까지의 회사·직무·연도만 허용하며 이름도 저장하지 않습니다. API 오류 시 `data/employment-public.json`의 확인된 공개 사례를 유지합니다. 브라우저는 기존 API로 최신 공개 자료를 갱신하며 실패 시 정적 사례를 유지합니다. 이메일, 연락처, 학번, Alumni ID, PIN은 빌드 출력에 포함하지 않습니다.

홈의 취업 미리보기에도 정적 사례가 포함됩니다. 공개 사례 수는 전체 취업률이 아니며 졸업예정자의 조기취업 자료는 정적 졸업생 사례에서 제외합니다.

## SEO·분석·검증

RSS에는 각 글의 본문 HTML(안전한 XML escaping), 원문 출처, guid, pubDate를 담습니다. sitemap의 lastmod는 공개 `content-manifest.json`의 내용 해시를 비교하여 실제 HTML 변경일에만 갱신합니다. 인사이트 글마다 관련 전공가이드 → 학생 프로젝트 → 입학안내를 연결합니다. 월·수·금 발행 방식은 유지하며 입시 시즌 편집 비율은 `tools/INSIGHT_EDITORIAL.md`를 따릅니다.

GA4: `admission_apply_click`, `admission_guide_click`, `admission_kakao_click`, `admission_phone_click`, `project_click`, `employment_click`, `portfolio_click`, `official_department_click`, `scroll_50`, `scroll_90`, `faq_open`, `admission_page_view`. 파라미터에는 클릭 영역만 보내며 학생 이름·연락처·이메일·입력값을 전송하지 않습니다. 기존 이벤트명에서 새 이름으로 전환되므로 GA4 보고서/주요 이벤트 설정은 확인이 필요합니다. 외부 UTM 유입은 GA4 기본 수집을 사용하고 내부 링크·canonical에는 붙이지 않습니다.

```sh
node tools/test_admission.cjs
python tools/test_insights.py
python tools/build_site.py
python tools/test_site.py
```

날짜 시뮬레이션: `BUILD_TIME=2026-11-11T00:00:00+09:00`; 외부 API 없는 재현 테스트: `OFFLINE_BUILD=1`. 테스트 실패 시 배포하지 않습니다. IndexNow는 배포된 sitemap을 읽어 URL/공개 key를 검증하고 429·5xx·연결 실패를 재시도합니다.
