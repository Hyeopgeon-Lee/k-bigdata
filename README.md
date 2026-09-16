# 빅데이터소프트웨어공학과 홍보 홈페이지

[![2027학년도 빅데이터소프트웨어공학과 수시 1차 모집](https://ai.k-bigdata.kr/assets/promo/og-share-2027-susi1.png)](https://apply.jinhakapply.com/Notice/5041044/A)

<p align="center">
  <a href="https://apply.jinhakapply.com/Notice/5041044/A"><img src="https://img.shields.io/badge/2027학년도%20수시%201차-원서접수%20바로가기-CBFF3D?style=for-the-badge&labelColor=071A33" alt="2027학년도 수시 1차 원서접수 바로가기"></a>
</p>

> **원서접수 2026.09.07 — 10.01 23:59** · 이미지를 누르거나 위 버튼을 선택하면 원서접수 페이지로 이동합니다.

한국폴리텍대학 서울강서캠퍼스 **빅데이터소프트웨어공학과** 홍보 홈페이지입니다.

- [학과 홈페이지](https://ai.k-bigdata.kr/)
- [졸업생 포트폴리오](https://portfolio.k-bigdata.kr/)
- [교수 기술 블로그](https://prof.k-bigdata.kr/)

## 주요 구성

- 2027학년도 수시 1차 일정과 원서접수 바로가기
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

`admission.js`는 한국시간 기준으로 수시 1차·2차·정시 접수 여부, 면접일, 최초 발표일, 마감 D-day와 버튼 링크를 갱신합니다. 일정은 2027학년도 공식 모집요강 기준입니다. 새 학년도는 공식 일정 발표 후 갱신해야 하며 기간 밖에는 모집요강으로 안내합니다. 동일 파일은 교수 블로그·포트폴리오에도 배포되어 있습니다.

## 공식 정보

- [학과 공식 홈페이지](https://www.kopo.ac.kr/kangseo/content.do?menu=1547)
- [2027학년도 모집요강](https://kopo.ac.kr/kangseo/content.do?menu=321)
- [온라인 원서접수](https://apply.jinhakapply.com/Notice/5041044/A)
- [입학 상담 오픈채팅](https://open.kakao.com/o/gEd0JIad)

> 입학 일정과 전형 기준은 대학 사정에 따라 바뀔 수 있으므로 공식 모집요강을 우선합니다.
