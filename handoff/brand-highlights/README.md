# 브랜드 섬네일 + 특장점 (Aside 조사, 2026-11-03)

## 클로드 코드에게: 이번에 할 일
바이어가 브랜드를 고를 때 "이 브랜드가 뭘 잘하는지" 바로 보이도록, 브랜드별 대표 이미지 1장과 짧은 특장점을 사이트에 붙인다.

1. `handoff/brand-highlights/brand_highlights.json`의 브랜드 25개 데이터를 `data/catalog.json`의 `brands` 배열에 합친다 (id로 매칭).
   - 추가 필드 제안: `thumb`(이미지 키 또는 경로), `tagline`, `strengths`(3개), `heroes`(대표 제품 2~3개: 이름 + 한 줄 포인트).
   - 기존 `desc`는 `desc_en`으로 교체하거나 그대로 두고 tagline을 추가. 판단해서 결정.
   - `*_kr` 필드, `confidence`, `image_status`, `image_note`, `thumb_source`는 내부 검수용. 사이트 JSON에는 넣지 않는다.
2. 섬네일: `thumbs/<id>.webp` 25장 (480px 정사각, 흰 배경, 기존 제품 썸네일과 같은 규격).
   - 제품이 있는 11개 브랜드는 기존 catalog.json 이미지 키를 그대로 썼다 (`thumb_source`에 키 기재). 새 파일 대신 그 키를 참조해도 된다.
   - On request 14개 브랜드는 외부 이미지를 받아 배경 정리 후 만든 새 파일. catalog.json의 `images`에 data URI로 넣거나 별도 파일로 두고 참조.
3. 화면 반영 (제안, 디자인은 기존 톤 유지):
   - 좌측 브랜드 레일에서 브랜드를 고르면 그리드 위에 **브랜드 소개 카드**: 섬네일 · 브랜드명 · tagline · 특장점 3개 · 대표 제품 칩.
   - 특히 "On request" 14개 브랜드는 지금 제품이 0개라 빈 화면이므로, 이 카드 + "Request product list" 버튼이 핵심 내용이 된다.
   - 모바일(≤960px)에서는 카드가 세로로 쌓이게.
   - (선택) 브랜드 전체 보기용 "Brands" 섹션: 25개 브랜드 카드 그리드.
4. 로컬에서 `python3 -m http.server 8810`로 확인 후 커밋·푸시.

## 지켜야 할 것 (HANDOFF.md 규칙 그대로)
- 브랜드 홈페이지 링크, 공급가·MOQ·바코드는 넣지 않는다. 이 폴더에도 출처 URL은 일부러 뺐다 (출처 목록은 대표님 PC의 Aside 산출물에 따로 있음).
- 수치·수상 문구(예: 누적 판매량, 어워드)는 브랜드사 발표·언론 보도 기준이다. `strengths_kr`에 (브랜드 주장)/(회사 발표) 표시가 있는 항목은 대표님이 브랜드사에 확인 전까지 그대로 두되, 새로 수치를 지어내지 않는다.
- `confidence: low`인 끄레뷰(crebeau)는 근거가 약하다. 브랜드사 소개서를 받으면 교체.

## 이미지 교체가 필요한 브랜드 (image_status: replace_later)
| 브랜드 | 이유 |
|---|---|
| charde | 구 패키지(MELAPEEL 표기). 리뉴얼 패키샷 요청 |
| eiom | 공식 흰 배경 패키샷 없음. 마케팅 이미지(한글 문구 포함)를 임시 사용 |
| phytos | 공식 이미지 해상도 낮음 |
| piciberry | 원본 500px로 작음 |

배경을 지운 이미지: lowlize, percentro, touchinsol, losykim(배지·스와치도 지움), donginbi(수상 배지 지움).

## 브랜드별 대표 제품 (요약)
| 브랜드 | 대표 제품(섬네일) | 한 줄 |
|---|---|---|
| ANUA (아누아) | Heartleaf 77% Soothing Toner | Heartleaf-powered soothing care for sensitive skin |
| Beauty of Joseon (조선미녀) | Relief Sun : Rice + Probiotics | Hanbang-inspired skincare and the Relief Sun range |
| Braye (브레이) | Thin Glow Tint | Effortless 'rough beauty' lip makeup in accessory-style packaging |
| CELIMAX (셀리맥스) | The Real Noni Energy Ampoule | Noni energy, Ji Woo Gae pore care and barrier skincare |
| Centellian24 (센텔리안24) | Madeca Cream | Centella derma skincare from a pharmaceutical company |
| Charde (샤르드) | Melacare Peel Cream Mask | Functional slow-aging care for dark spots and firmness |
| crebeau (끄레뷰) | Water Active Cream | Placenta and pearl skincare |
| DONGINBI (동인비) | Red Ginseng Daily Defense Capsule Ampoule | Korean red ginseng skincare from KGC (Jung Kwan Jang) |
| Dr.Althea (닥터엘시아) | 345 Relief Cream | Gentle derma skincare for sensitive, blemish-prone skin |
| EIOM (이옴) | Trouble Patch Mask | Microbiome-based blemish care, led by a patch mask |
| FRANZ (프란츠) | Stem Cell Culture Medium Ampoule | Doctor-developed patches, trouble care and ampoules |
| JENNYHOUSE (제니하우스) | Salon Spa Shine Silk Hair Oil | Cheongdam salon expertise for home hair care and color |
| KEYM (키임) | Lip Glow Bow | Bow-shaped lip glow you can wear as a keyring |
| KITSCH CATCH (키치캐치) | Cheeky Color Balm | Playful eyeshadows and color balms |
| KUNDAL (쿤달) | Honey & Macadamia Pure Body Wash | Fragrance-led hair and body care with honey & macadamia |
| Losy Kim (로지킴) | PDRN Tinted Lip Ampoule | Healthy-glow makeup with skincare ingredients |
| Lowlize (로우라이즈) | Skin Repair Serum | Clean, soothing skincare for the moisture barrier |
| medicube (메디큐브) | Zero Pore Pad 2.0 | Derma skincare lines and AGE-R home beauty devices |
| MIXSOON (믹순) | Bean Essence | Single-ingredient essences, vegan certified |
| percentro (퍼센트로) | Wrinkle RED Mask | Sheet masks with clinical results on the box |
| Phytos (피토스) | Phytopecia Plus Hair Boosting Shampoo | P1P bio-technology scalp care and skincare |
| piciberry (피치베리) | Berry Shadow | Multi-use pastel makeup by a makeup artist |
| TAM BEAUTY (탐뷰티) | The Jelly Plumping Lip Oil | Jelly-texture lip oils, glosses and cushions |
| too cool for school (투쿨포스쿨) | Artclass By Rodin Shading | Art-driven Seoul makeup since 2009 |
| Touch in Sol (터치인솔) | No Poreblem Primer Prep | Base makeup led by a pore-blurring primer |
