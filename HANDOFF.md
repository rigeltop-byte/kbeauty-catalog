# K-Beauty Trade Catalog — 클로드 코드 인수인계

## 목적
화장품 유통 법인(김종훈·양정훈 대표 공동 설립 예정)의 **바이어용 제품 카탈로그 사이트**.
해외 바이어가 브랜드·카테고리·검색으로 제품을 고르고, 문의 목록을 만들어 복사한 뒤 이메일·메신저로 보내는 방식.
claude.ai 아티팩트로 1차본을 만들었으나, **Claude 계정 없이 누구나 열 수 있는 주소**가 필요해 GitHub Pages로 옮긴다.

## 이번에 할 일 (클로드 코드에게)
1. 이 폴더를 새 GitHub 저장소로 올린다 (예: `kbeauty-catalog`). 무료 플랜 GitHub Pages는 **public 저장소**가 필요하다.
2. Settings → Pages → Source: `Deploy from a branch`, Branch: `main`, 폴더: `/ (root)`.
3. 몇 분 뒤 `https://<계정>.github.io/kbeauty-catalog/` 에서 열리는지 확인 (로그인하지 않은 시크릿 창으로).
4. 확인 후 대표님께 주소 전달.
5. (선택) 회사 도메인이 정해지면 Pages의 Custom domain에 연결.

## 폴더 구조
```
index.html          완성된 단일 페이지 (HTML/CSS/JS 모두 포함, 외부 의존은 Google Fonts뿐)
data/catalog.json   브랜드 25개 · 제품 877개 · 제품 썸네일(webp, data URI 내장) — 약 3MB
.nojekyll           GitHub Pages가 Jekyll 처리를 하지 않도록
.gitignore          원본 엑셀·CSV가 실수로 올라가지 않도록 차단
tools/              데이터 재생성 스크립트 (아래 참고)
```
- `index.html`은 `fetch('data/catalog.json')`으로 데이터를 읽으므로 **로컬에서 파일 더블클릭으로는 안 열리고**, `python3 -m http.server`로 띄워서 확인한다.

## 절대 공개하면 안 되는 정보 (가장 중요)
저장소가 public이므로 아래 항목은 **index.html, catalog.json, 커밋 이력 어디에도** 들어가면 안 된다.
- 공급가(Supply / Offer / FOB / Distributor price), 최소주문금액(MOQ/MOA), 바코드, 내부 메모
- 원본 가격표 엑셀(`발송용_화장품_제품_제안_price.xlsx`, `메이저_화장품_브랜드_제안_price.xlsx`)과 정리 CSV(`화장품_유통가능_SKU_전체목록.csv`)
- 브랜드 홈페이지 링크 (바이어가 브랜드사에 직접 연락하는 것을 막기 위해 의도적으로 뺐음)

현재 catalog.json의 필드:
- 제품: `b` 브랜드ID, `c` 카테고리, `l` 원본 라인명, `n` 영문명, `k` 국문명, `v` 용량, `p` 소비자가(MSRP, USD), `i` 이미지 키
- 브랜드: `id, name, kr, desc, count, cats, note(판매 제한), nmpa(중국 등록)`
커밋 전 확인: `grep -ri "supply\|fob\|moq\|barcode" data/` 결과가 비어 있어야 한다.

## 표시 정책 (대표님 확인 사항)
- 소비자가(MSRP)는 표시 중 — 빼달라고 하시면 `index.html`의 `.price` 렌더링과 정렬 옵션 제거.
- 아누아: "한국 내수 판매 불가, 러시아 온라인 판매 불가" 조건 표시.
- 단가표가 없는 14개 브랜드: "List on request" + 제품 목록 요청 버튼.
- 회사명·연락처 미정 → 상단 로고는 임시로 "K-Beauty Trade Catalog". 정해지면 `.mark`, `<title>`, 문의 안내 문구, 복사 텍스트 첫 줄(`inquiryText()`)을 교체.
- `<meta name="robots" content="noindex">`로 검색엔진 노출을 막아 두었다 (링크 받은 바이어만 보도록). 공개 홍보용으로 바꿀 때 제거.

## 데이터 갱신 (새 가격표가 오면)
`tools/` 스크립트는 claude.ai 세션에서 쓰던 그대로라 **경로를 로컬에 맞게 고쳐야 한다**. 원본 엑셀은 저장소 밖(예: `../source/`)에 두고 돌린다.
1. `normalize.py <out.csv>` — 시트별 컬럼 매핑(MAP)으로 SKU 정규화, 행 번호 기록
2. `extract_images.py <imgmap.json> <xlsx...>` — 셀 내 이미지(richData)와 떠 있는 이미지(drawing)를 행에 매핑
3. 행-이미지 결합 → `build/rows_img.json` (쿤달은 같은 라인 내 이미지 이어받기)
4. `make_thumbs.py` — 배경 잘라내고 480px 정사각 흰 캔버스 webp
5. `build_data.py` — 공급가·바코드 제외하고 `site/data/catalog.json` 생성, 카테고리 자동 분류(CATS 키워드)
새 브랜드 시트가 추가되면 `normalize.py`의 `MAP`과 `build_data.py`의 `BRANDS`에 한 줄씩 추가.

## 알려진 남은 일
- 이미지가 없는 제품 24개(원본에 이미지 없음 또는 EMF 형식) → 브랜드명 자리표시로 나옴
- 닥터엘시아 "나이아치온 크림 30ml"은 원본 공급가 값이 이상함(내부 확인용, 사이트엔 영향 없음)
- 문의는 현재 "복사해서 보내기" 방식. 접수 자동화가 필요하면 Formspree·Google Forms·Tally 같은 폼 서비스나 간단한 백엔드 연결 검토
- 다국어(러시아어 등) 필요 시 UI 문구를 사전 객체로 분리

## 디자인 개편 (2026-11-03, Claude Code)
모빈(Mobbin) 레퍼런스 — Faire(도매 B2B 카탈로그)·Selfridges·lululemon(좌측 필터 레일), Hims/Hers(따뜻한 오프화이트 톤, 연회색 제품 웰, 카트 드로어) — 를 기준으로 `index.html`의 CSS·마크업을 다시 썼다. 데이터(`data/catalog.json`)와 기능(검색·브랜드/카테고리 필터·정렬·문의 목록·복사)은 그대로다.
- 서체: 헤드라인·브랜드명 Fraunces(세리프), 본문 DM Sans, 국문 IBM Plex Sans KR. 다크 모드는 뺐다(라이트 고정).
- 레이아웃: 상단 바(로고·검색·문의 버튼) → 세리프 히어로 + 숫자 3개 → 좌측 고정 레일(브랜드 25개 + 카테고리, 각 수량 표시) + 우측 제품 그리드. 960px 이하에서는 레일 대신 가로 스크롤 칩 두 줄.
- 제품 카드: 연회색 웰 위에 이미지 `mix-blend-mode: multiply`(흰 배경 썸네일이 자연스럽게 섞임), 좌상단 카테고리 배지, 브랜드 → 영문명 → 국문명 → 용량·MSRP → "Add to inquiry" 알약 버튼.
- 문의 드로어: 항목별 수량 −/+ 스테퍼, "Your details" 폼, 복사 버튼(장미색).
- 로컬 확인: `.claude/launch.json`의 `kbeauty-catalog`(포트 8810) 또는 `python3 -m http.server 8810 --directory kbeauty-catalog`.
- 회사명이 정해지면 바꿀 곳: `.mark .name`, `<title>`, `footer .fm`, `inquiryText()` 첫 줄.
