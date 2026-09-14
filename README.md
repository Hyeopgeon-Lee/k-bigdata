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

GitHub Actions가 **매주 월·수·금 오전 6시(한국시간)**에 최신 AI·데이터·클라우드 기사를 확인합니다. 타 대학·학교·연구팀 사례가 제목에 포함된 기사는 자동으로 제외합니다. 선택한 기술 흐름은 문제 설명, 핵심 기술, 학과 프로젝트 적용과 학습 체크포인트를 갖춘 글로 구성해 `data/posts.json`에 발행합니다.

배포할 때 `tools/build_site.py`가 다음 결과물을 자동 생성합니다.

- `/insights/` 전체 글 목록과 `/insights/글주소/` 형식의 고유 정적 게시글
- 제목·설명·작성 조직·발행일이 포함된 `BlogPosting` 구조화 데이터
- 홈페이지 최신 글 카드와 주제별 관련 글
- 신규 글과 `lastmod`가 포함된 `/sitemap.xml`
- 네이버와 RSS 구독기가 확인할 수 있는 `/feed.xml`

기존 `post.html?slug=...` 주소는 대응하는 새 정적 주소로 자동 이동합니다. 사이트맵과 RSS는 빌드 결과물이므로 저장소에서 직접 수정하지 않습니다.

자동 발행은 `Actions` 탭의 `학과 홈페이지 자동 발행`에서 수동으로도 실행할 수 있습니다. GitHub의 실행 상황에 따라 예약 시각보다 수 분 늦게 게시될 수 있습니다.

## 공식 정보

- [학과 공식 홈페이지](https://www.kopo.ac.kr/kangseo/content.do?menu=1547)
- [2027학년도 모집요강](https://kopo.ac.kr/kangseo/content.do?menu=321)
- [온라인 원서접수](https://apply.jinhakapply.com/Notice/5041044/A)
- [입학 상담 오픈채팅](https://open.kakao.com/o/gEd0JIad)

> 입학 일정과 전형 기준은 대학 사정에 따라 바뀔 수 있으므로 공식 모집요강을 우선합니다.
