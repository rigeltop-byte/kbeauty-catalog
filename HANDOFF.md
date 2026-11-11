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
확정(대표, 2026-11-05): 조선미녀 "Revive Eye Serum : Ginseng + Retinal"(국문 표기 인삼아이크림)은 영문 공식명대로 Serums & Ampoules에 둔다. 크림으로 옮기지 않는다.
재실행: `python3 -I tools/enrich.py data/catalog.json --report` (바뀐 항목 목록 출력).

## 다음 작업: 텍스처·리뷰 인사이트 (2026-11-11, Aside 조사)
대표 요청: 제형·발림성·마무리감을 점 척도(예: Smooth ↔ Sticky)로 가독성 있게 보여주고 AI 리뷰 요약을 추가.
- 작업 지시서: `handoff/review-insights/README.md` (먼저 읽기, 1장 법·약관 원칙 필수)
- 데이터: `handoff/review-insights/review_insights.json` — 제품 14개(23개 SKU) + 제품 목록 없는 브랜드 대표 제품 7개
- 목업: `handoff/review-insights/mockup.html` (카드 + 상세 패널)
- 플랫폼명·별점·리뷰 원문 금지, AI 요약 면책 문구 필수, `summary_kr`·`sentiment`는 사이트에 넣지 않음
- 공개 저장소 게시는 대표 승인 후

### 반영 결과 (2026-11-11, Claude Code)
- `python3 -I tools/apply_insights.py --catalog data/catalog.json --insights handoff/review-insights/review_insights.json` (`--dry-run`은 매칭만 확인). 여러 번 돌려도 결과가 같다. 결과: 제품 14개 전부 매칭, **SKU 23개**에 `ins`, 브랜드 7곳에 `heroIns`, 척도 정의 18개는 최상위 `scales`, 기준 월은 `insUpdated`.
  - 제품 `ins` = `{kind, vol, sc:[[척도키, 1~5]], tl, loved, gtk, best, sum, note?}`. `summary_kr`·`sentiment`는 복사하지 않고, 새어 나가면 스크립트가 멈춘다.
  - 이름이 안 맞으면 `WARNING: no catalog product named …`(가까운 이름 제안)로 알리고 건너뛴다.
  - 문구 점검: 리뷰 출처명·별점 표현·효능이나 의약품처럼 보이는 단어(cure, treat, heal, repair, redness, blackhead, improve 등)가 데이터에 있으면 **쓰기 전에 멈춘다**. 걸리면 `review_insights.json` 문구를 고치고 다시 돌린다. 출처명 목록은 `handoff/review-insights/banned_terms.json`에 따로 둔다(공개 저장소에 올라가지 않음). 제품 공식명(예: Skin Repair Serum)은 점검하지 않는다.
- 화면(`index.html`)
  - 제품 카드: 국문명 아래 `tl` 한 줄(2줄 말줄임) → 척도 2개 → "Texture & review insight →". 링크는 척도 바로 아래에 두었다(목업은 버튼 아래). 인사이트 없는 카드와 한 줄에 섞여도 가격·"Add to inquiry" 버튼 높이가 맞도록 하기 위해서다. 인사이트 없는 제품은 기존 카드 그대로.
  - 상세 패널(`#insight`): 데스크톱은 오른쪽 드로어, 640px 이하는 바텀시트. 순서는 지시서와 같다(헤더 → Texture & feel 전체 척도 + (i) 설명 → Loved for → Best for → Good to know → AI Review Insight → 면책 문구 → Add to inquiry). Esc·바깥 클릭으로 닫히고 닫으면 원래 링크로 포커스가 돌아간다.
  - 척도: `scaleRow()` 하나로 그린다. bipolar는 선 위 5칸 중 한 칸(장미색), level은 점 채움. `role="img"` + `aria-label`("Skin feel: 2 of 5, between Smooth and Sticky" / "Hydration: 4 of 5"). 별·점수처럼 보이는 표시는 쓰지 않았다.
  - 브랜드 소개 카드: `heroIns`가 있으면 카드 아래쪽에 대표 제품 인사이트(척도 전체·Loved for·Best for·Good to know·AI 요약·면책 문구).
  - 필터: 레일 맨 위 "Texture" 상자(모바일은 칩 한 줄 추가). "Texture insight" 스위치 + Lightweight(texture≤2)·Non-sticky(feel≤2)·Dewy finish(finish≥4)·Extra gentle(gentleness≥4). 칩은 여러 개 고르면 모두 만족하는 제품만. 숫자는 현재 브랜드·그룹·분류 안에서의 개수. 조건은 `TEX` 배열 한 곳에서 고친다.
  - 푸터에 "척도·리뷰 인사이트는 공개 소비자 의견을 우리가 요약한 것이며 제품 효능 주장이 아니다" 한 문장 추가.
- 확인: 375px·1440px 스크린샷 `handoff/review-insights/screenshots/`. 기존 기능(검색·브랜드/그룹/분류 필터·정렬·더 보기·문의 담기·수량·복사·새로고침 후 유지)은 수정 전후 화면을 같은 순서로 조작해 결과가 같은지 비교했다(20개 항목 일치).
- 안 한 것: 문의 복사 텍스트에 `texture_line` 넣기(지시서 "추가하면 좋은 기능" 2번), 척도 비교(3번), 이미지 위 "Insight" 배지(선택 항목).

### 문구 정리와 공개 게시 (2026-11-11, 대표 승인)
- 문구 기준(대표 지시): 피부 상태에 대한 **효능 주장 대신 사용감**으로 쓴다. 고친 10곳:
  - 아누아 토너 요약 "calms redness" → "leaves a soothing, comforting feel"
  - 아누아 클렌징 오일 "Helps with blackheads" → "Pore-clearing feel", 요약 "Blackhead care is a frequently mentioned benefit" → "A clean, pore-clearing feel is frequently mentioned"
  - 닥터엘시아 345 요약 "calms post-blemish skin" → "feels comfortable on blemish-prone skin"
  - 아누아 나이아신아마이드 세럼 "targets uneven tone" → "made for a brighter-looking finish", "Visible tone improvement" → "Brighter-looking tone"
  - 메디큐브 PDRN 세럼 "Tone improvement" → "More even-looking tone"
  - 메디큐브 제로 모공 패드 "Pore care" → "Clean-pore feel", 요약 "visibly refined pores" → "a clean-pore feel"
  - 믹순 순디 에센스 Best for "Sensitive and irritated skin" → "Sensitive, easily irritated skin"
  - 그대로 둔 것: "Calming"·"Healthy glow"·"Gentle exfoliation" 같은 일반 화장품 표현, 주의 문구(예: 일부 사용자의 트러블 언급), 제품 공식명.
- 게시: `kbeauty-catalog/`에서 `handoff/`를 빼고 공개 저장소 `rigeltop-byte/kbeauty-catalog` main에 복사·커밋·푸시(커밋 `1045226`). GitHub의 "pages build and deployment"가 그 커밋으로 성공(2026-11-11 09:05 UTC). 공개 주소 반영은 대표가 직접 확인했다(Texture 필터 23개, 인사이트 카드 표시, 플랫폼명 없음). 작업한 클라우드 세션에서는 `rigeltop-byte.github.io` 접속이 막혀 있어 페이지를 직접 열지 못했고, 네트워크 허용 설정은 대표 지시로 하지 않았다.
- 게시 전 확인
  - `grep -ri "supply\|fob\|moq\|barcode" data/`는 **비어 있지 않다**. 190건 모두 `images`의 base64 이미지 글자열 안에서 우연히 맞은 것이고(이전 게시본도 같은 190건, 이미지 데이터는 이전 게시본과 동일), 이미지 밖의 텍스트·키에는 0건이다. 다음부터는 이미지 값을 빼고 검사해야 의미가 있다: `python3 -c "import json,re;d=json.load(open('data/catalog.json'));d.pop('images');print(re.findall(r'(?i)supply|fob|moq|barcode',json.dumps(d,ensure_ascii=False)))"` → `[]`.
  - 제품 필드는 이전 게시본에서 `ins`만 늘었다(공급가·바코드 필드 없음).
  - 인사이트 화면(카드 23개, 상세 패널 23개, 브랜드 대표 제품 7곳)에 플랫폼명·별점 없음, 면책 문구 전부 표시.
- 브랜드 소개 카드의 평점 숫자 정리(2026-11-11, 대표 지시): Losy Kim "Musinsa rating 4.8 with 1,000+ reviews" → "Strong customer reviews in Korea", Lowlize "High Musinsa ratings: serum 4.8, sun serum 4.9" → "Strong customer reviews in Korea for the serum and sun serum". `handoff/brand-highlights/brand_highlights.json`을 고치고 `tools/apply_brands.py`를 다시 돌렸다(바뀐 것은 이 두 줄뿐). 브랜드 카드에 다른 평점·리뷰 수 숫자는 없다. 유통 채널 사실(Olive Young 입점 등 6곳)은 대표 결정으로 그대로 둔다. 앞으로 브랜드 카드에도 평점·리뷰 수 숫자는 쓰지 않는다.
- 남아 있는 것(참고): 플랫폼 순위 문구 2곳 — Charde "ranks #1 on its Musinsa brand page", EIOM "#1 in category on Qoo10 Japan". 평점·리뷰 수가 아니라서 이번에는 두었다.
- 다음에 게시할 때: 공개 저장소를 쓰기 권한으로 연결 → `handoff/`만 빼고 폴더 내용을 덮어쓰기 → 위 검사 → 커밋·푸시.
