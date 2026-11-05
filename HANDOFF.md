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
- 제품: `b` 브랜드ID, `g` 그룹(Skincare / Makeup / Hair & Body / Sets & More), `c` 카테고리(아래 「카테고리 체계」 참고), `l` 원본 라인명, `n` 영문명, `k` 국문명, `v` 용량, `p` 소비자가(MSRP, USD), `i` 이미지 키, `ir` 1이면 같은 제품의 다른 용량·향 사진을 대신 쓴 것(카드에 "Representative photo" 표시)
- 최상위: `groups` 그룹 순서 배열
- 브랜드: `id, name, kr, desc, count, cats, note(판매 제한), nmpa(중국 등록)` + 특장점 카드용 `thumb`(이미지 키), `tagline`, `strengths`(3줄), `heroes`([{n, note}] 대표 제품), `focus`
커밋 전 확인: `grep -ri "supply\|fob\|moq\|barcode" data/` 결과가 비어 있어야 한다.

## 표시 정책 (대표님 확인 사항)
- 소비자가(MSRP)는 표시 중 — 빼달라고 하시면 `index.html`의 `.price` 렌더링과 정렬 옵션 제거.
- 아누아: "한국 내수 판매 불가, 러시아 온라인 판매 불가" 조건 표시.
- 단가표가 없는 14개 브랜드: "List on request" + 제품 목록 요청 버튼.
- 회사명·연락처 미정 → 상단 로고는 임시로 "K-Beauty Trade Catalog". 정해지면 `.mark`, `<title>`, 문의 안내 문구, 복사 텍스트 첫 줄(`inquiryText()`)을 교체.
- `<meta name="robots" content="noindex">`로 검색엔진 노출을 막아 두었다 (링크 받은 바이어만 보도록). 공개 홍보용으로 바꿀 때 제거.

## 이미지·분류 파이프라인 (2026-11-03 개편)
썸네일은 `tools/make_thumbs.py`(혼합 방식)로 만든다. 흰 배경은 자르기만 하고, 회색·분홍 단색 배경은 macOS Vision 누끼(`tools/cutout.swift`)가 제품 범위와 맞을 때만 쓰며, 아니면 좁은 허용치로 배경색만 지운다. 사진 배경은 Vision 누끼를 쓴다.
1. 원본 추출: 엑셀 `xl/media/*`를 md5[:12] 키로 `build/orig/<key>.<ext>`에 저장 (카탈로그의 이미지 키와 같다)
2. `swiftc -O -o cutout tools/cutout.swift && ./cutout build/cut build/orig/*` (맥 전용, 674장 30초)
3. `python3 tools/make_thumbs.py --orig build/orig --cut build/cut --out build/thumbs --review build/review` → 리뷰 시트 `sheet_<방식>.jpg`로 눈 검수
4. `python3 tools/apply_images.py --catalog data/catalog.json --thumbs build/thumbs --extra build/extra` → 썸네일 교체, 공식 사진 추가(`extra.json` 매핑), 형제 제품 사진 대체(`ir`), `tools/enrich.py`로 그룹·세부 분류 부여
- 시스템 파이썬(`/usr/bin/python3`, Pillow·numpy·openpyxl 있음)으로 돌린다. Homebrew 파이썬에는 패키지가 없다.
- 공식 사진 출처: medicube.us, celimax.us, celimax.com 제품 페이지의 대표 이미지 7장(PDRN Hydrating UV Serum, 3H Drying Lotion, Rosemary PDRN Hair Mask, Ji Woo Gae One Step Mild Cleansing Pad, Baking Soda Deep Pore Foam, Vita-A Retinal Shot Dual Cream, Noni Calming Glow Pad).
- 아직 사진이 없는 제품: medicube SOS Invisible Patch 36pcs 1개(공식 사이트에 없음).
- 누끼가 제품을 잘라먹은 61장(마스크팩 봉지, 펌프·뚜껑만 남은 병, 키치캐치 팔레트 등)은 `tools/thumb_overrides.json`에 키를 적어 두어 '안전 모드'(배경 제거 없이 자르기만, 배경색 캔버스)로 만든다(2026-11-04). 새로 잘린 게 보이면 그 키를 이 파일에 추가하고 다시 돌린다. 대체 사진(브랜드 공식 흰 배경 컷)이 오면 `build/orig`의 원본을 바꾸고 목록에서 뺀다.

## 바이어 탐색 구조 (2026-11-03)
- 브랜드 레일(좌측) → 그룹 탭(All / Skincare / Makeup / Hair & Body / Devices / Sets & more, 수량 표시) → 그룹별 세부 분류(레일 "Categories"가 그룹 머리글로 묶여 보이고, 그룹을 고르면 그 그룹의 분류만 남음) → 검색·정렬.
- 모바일(≤960px)은 그룹 탭이 가로 스크롤, 분류는 칩 두 줄.
- 분류 규칙은 `tools/enrich.py`의 `GROUP`·`MAKEUP` 표. 새 분류가 생기면 거기에 한 줄 추가.
- 이름에 "사용중지"·"단종"이 붙은 제품은 `enrich.py`가 카탈로그에서 뺀다(2026-11-03 기준 메디큐브 PDRN 펩타이드 글로시 립 밤 1개). (KR)/(US) 표시는 기기 전압 규격 차이라 그대로 둔다.

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

## 다음 작업: 브랜드 섬네일 + 특장점 카드 (2026-11-03, Aside 조사)
대표님 요청: 브랜드별로 섬네일 이미지 1장과 간략한 제품 특장점을 사이트에 넣기.
- 작업 지시서: `handoff/brand-highlights/README.md` (먼저 읽기). **이 폴더는 시하기획-OS에만 있고 공개 저장소에는 올리지 않는다**(국문 검수 메모·신뢰도·이미지 출처 포함). 공개 저장소로 동기화할 때 `--exclude 'handoff/'`.
- 데이터: `handoff/brand-highlights/brand_highlights.json` — 25개 브랜드의 tagline, 소개, 특장점 3개, 대표 제품 2~3개(영문 바이어용 + 국문 검수용)
- 섬네일: `handoff/brand-highlights/thumbs/<브랜드id>.webp` 25장 (480px 정사각 흰 배경, 기존 제품 썸네일 규격)
- 핵심: 제품 0개인 "On request" 14개 브랜드도 소개 카드가 생기도록. 브랜드를 고르면 그리드 위에 소개 카드 표시
- 이미지 교체 대기: charde(구 패키지), eiom(마케팅 이미지), phytos(저해상도), piciberry(작은 원본)
- 수치·수상 문구는 브랜드사 발표·보도 기준. 지어내지 말고, 출처 URL·브랜드 홈페이지 링크는 넣지 않는다

### 반영 결과 (2026-11-04, Claude Code)
- `tools/apply_brands.py --catalog data/catalog.json --highlights handoff/brand-highlights`가 25개 브랜드를 병합한다. 제품이 있는 11개는 기존 이미지 키를 `thumb`로 쓰고, On request 14개는 `thumbs/<id>.webp`를 data URI로 `images`에 넣는다(키 = md5[:12]). `*_kr`·`confidence`·`image_status`·`thumb_source`는 사이트 JSON에 넣지 않는다.
- 화면: 브랜드를 고르면 그리드 위 소개 카드(썸네일 · 분야/제품 수 · 브랜드명 · tagline · 소개 · 특장점 3개 · 대표 제품 칩). 제품이 있는 브랜드는 대표 제품 칩을 누르면 그 이름으로 검색된다. On request 브랜드는 카드 + "Request product list"가 본문이다. ≤960px 두 열, ≤640px 한 열.
- 브랜드 데이터가 바뀌면 `brand_highlights.json`을 고치고 위 스크립트를 다시 돌린 뒤 커밋.
- 이미지 교체 대기(charde·eiom·phytos·piciberry)와 lowlize(누끼 거침)는 새 사진이 오면 `thumbs/<id>.webp`만 바꾸고 다시 돌린다.
- (선택) 25개 브랜드 카드 그리드("Brands" 섹션)는 아직 안 했다.

## 카테고리 체계 (2026-11-04, 대표 지시로 재분류)
`tools/enrich.py`가 제품명(영문 `n`·국문 `k`, 일부 라인명 `l`)을 키워드 규칙으로 읽어 `c`(카테고리)·`g`(그룹)를 다시 매긴다. `data/catalog.json`의 `groups`·`catOrder`가 사이트 레일의 표시 순서다.
- 스킨케어(Skincare): Serums & Ampoules / Masks & Patches / Toners, Pads & Mists / Creams & Essences / Sun Care / Cleansing
- 메이크업(Makeup): Base / Lip / Eye / Cheek & Point
- 헤어·바디(Hair & Body): Hair Care / Body Care / Devices & Tools
- 세트·기타(Sets & More): Sets & Kits(기획세트·트라이얼 키트·샘플 샤쉐) / Other(가글·티슈·파우치·화장솜·펌프)
규칙 순서가 중요하다: 립 → 세트 → 헤어 → 바디 → 마스크·패치 → 아이·치크·베이스 → 선케어 → 토너·미스트 → 클렌징 → 크림(영문명에 cream/lotion/moisturizer) → 세럼·앰플·오일·파우더 → 나머지 크림·에센스. 에센스는 대표 지시대로 크림과 한 묶음, 믹순 파우더는 세럼·앰플(부스터)로 둔다.
판단 보류 1건: 조선미녀 "Revive Eye Serum : Ginseng + Retinal"(국문 표기 인삼아이크림)은 영문 공식명이 아이세럼이라 Serums & Ampoules에 두었다. 크림으로 옮기려면 `classify()` 12번 규칙의 `not has(n, 'serum')` 예외를 빼거나 제품명을 고친다.
재실행: `python3 -I tools/enrich.py data/catalog.json --report` (바뀐 항목 목록 출력).
