"""Build buyer-safe catalog.json (no supply price, barcode, MOQ or internal notes)."""
import json, re, base64, os, collections

ROWS = json.load(open('build/rows_img.json'))
OUT = 'site/data/catalog.json'
os.makedirs('site/data', exist_ok=True)

HANGUL = re.compile(r'[가-힣]')
HAN = re.compile(r'[一-鿿]')


def tidy(s):
    return ' '.join((s or '').split()).strip(' -/')


def split_multi(s):
    """'EN text 한글 텍스트 中文' -> (en, kr)"""
    m = HANGUL.search(s)
    if not m:
        return s, ''
    en, rest = s[:m.start()], s[m.start():]
    h = HAN.search(rest)
    kr = rest[:h.start()] if h else rest
    return tidy(en), tidy(kr)


def clean_kr(s, brand):
    s = re.sub(r'^제품국내\[[^\]]*\]', '', s)
    s = re.sub(r'V\d{3}$', '', s)
    s = re.sub(r'^조선미녀_', '', s)
    s = s.replace('{KR)', '(KR)')
    return tidy(s)


VOL = re.compile(r'(\d+(?:\.\d+)?\s?(?:ml|mL|ML|g|G|kg|KG|ea|EA|pcs|PCS|매|sheets?))\b')

CATS = [
    ('Devices & Tools', ['booster pro', 'v roller', 'ultra tune', 'focus shot', 'device', 'diagnosis', 'cleanser head', 'beauty tool', 'mah', 'derma booster', 'brush']),
        ('Hair Care', ['shampoo', 'hair', 'scalp', 'conditioner', 'jennyhouse', 'treatment']),
    ('Home & Lifestyle', ['diffuser', 'perfume', 'fragrance', 'toothpaste', 'oral', 'detergent', 'fabric', 'softener', 'wipe', 'tissue', 'pet ', 'baby lotion', 'baby wash', 'baby bath', 'air fresh', 'mouth', 'laundry']),
    ('Sun Care', ['sun', 'spf', ' uv']),
    ('Makeup', ['lip', 'cushion', 'eyeshadow', 'eye shadow', 'mascara', 'brow', 'tint', 'blush', 'foundation', 'palette', 'color balm', 'gloss', 'concealer', 'makeup', 'liner', 'highlighter', 'shading', 'primer', 'glitter', 'cheeky']),
    ('Sets & Kits', [' set ', ' set(', ' kit ', ' kit(', 'trial kit', ' skin duo', 'cleansing duo', 'suit case']),
    ('Body & Hand', ['body', 'hand cream', 'hand wash', 'hand ', 'scrub', 'feminine', 'deodor', 'foot']),
    ('Masks & Patches', ['mask', 'patch', 'sheet', ' pack ']),
    ('Cleansing', ['cleans', 'foam', 'wash', 'peel', 'exfoliat', 'micellar', 'remover']),
    ('Toners, Pads & Mists', ['toner', 'pad', 'skin conditioning', 'essence water', 'mist', 'spray', 'milk']),
    ('Serums & Ampoules', ['serum', 'ampoule', 'ampule', 'essence', 'booster', 'oil', 'spicule', 'shot', 'seum']),
    ('Creams & Moisturizers', ['cream', 'lotion', 'gel', 'balm', 'emulsion', 'moistur']),
]


def category(r, en):
    hay = (' ' + (r['category'] or '') + ' ' + en + ' ' + r['brand'] + ' ').lower()
    for name, keys in CATS:
        if any(k in hay for k in keys):
            return name
    return 'Other'


BRANDS = {
    'JENNYHOUSE 제니하우스': ('jennyhouse', 'JENNYHOUSE', '제니하우스', 'Salon hair color and hair care developed by the Jenny House salon in Cheongdam, Seoul.'),
    'FRANZ 프란츠': ('franz', 'FRANZ', '프란츠', 'Patches, trouble care and masks developed in collaboration with doctors. Supplied to Olive Young, Costco and TJ Maxx.'),
    'KUNDAL 쿤달': ('kundal', 'KUNDAL', '쿤달', 'Fragrance-led hair and body care with strong global sales, plus home and lifestyle lines.'),
    'TAM BEAUTY 탐뷰티': ('tambeauty', 'TAM BEAUTY', '탐뷰티', 'Jelly-texture lip oils, glosses and cushions.'),
    'KITSCH CATCH 키치캐치': ('kitschcatch', 'KITSCH CATCH', '키치캐치', 'Playful eyeshadows and color balms.'),
    'medicube 메디큐브': ('medicube', 'medicube', '메디큐브', 'Derma skincare lines (Zero Pore, PDRN, Collagen, Kojic Acid) and AGE-R home beauty devices.'),
    'MIXSOON 믹순': ('mixsoon', 'MIXSOON', '믹순', 'Single-ingredient essences such as Centella, Bean and Bifida. Vegan certified.'),
    'Dr.Althea 닥터엘시아': ('dralthea', 'Dr.Althea', '닥터엘시아', 'Gentle derma skincare: cleansers, toners, pads, serums and SPF.'),
    'CELIMAX 셀리맥스': ('celimax', 'CELIMAX', '셀리맥스', 'Noni energy line, Ji Woo Gae pore care and barrier skincare.'),
    'ANUA 아누아': ('anua', 'ANUA', '아누아', 'Heartleaf soothing toners, cleansing oils and targeted serums.'),
    'Beauty of Joseon 조선미녀': ('beautyofjoseon', 'Beauty of Joseon', '조선미녀', 'Hanbang-inspired skincare and the Relief Sun range.'),
}
RESTRICT = {'anua': 'Not for sale in the Korean domestic market. No online sales in Russia.'}

# Brands on the brand list without a product sheet yet
LIST_ONLY = [
    ('touchinsol', 'Touch in Sol', '터치인솔', ['Skincare', 'Makeup Base', 'Lip', 'Eye', 'Sun Care'], ''),
    ('donginbi', 'DONGINBI', '동인비', ['Skincare', 'Sun Care', "Men's Care"], 'By KGC (Korea Ginseng Corporation), rich in the main components of red ginseng.'),
    ('percentro', 'percentro', '퍼센트로', ['Mask Pack'], 'Recommended items on Musinsa.'),
    ('toocoolforschool', 'too cool for school', '투쿨포스쿨', ['Makeup Base', 'Eye', 'Lip', 'Sun Care', 'Body Care', 'Hair Care', 'Skincare', 'Mask Pack', 'Accessories'], ''),
    ('piciberry', 'piciberry', '피치베리', ['Skincare', 'Mask Pack', 'Makeup Base', 'Eye', 'Lip', 'Blusher', 'Accessories'], ''),
    ('centellian24', 'Centellian24', '센텔리안24', ['Skincare', 'Sun Care', 'Mask Pack', 'Body Care'], 'Skincare developed by a pharmaceutical company.'),
    ('losykim', 'Losy Kim', '로지킴', ['Makeup Base', 'Lip'], ''),
    ('braye', 'Braye', '브레이', ['Makeup Base', 'Lip', 'Perfume', 'Nail', 'Accessories'], ''),
    ('keym', 'KEYM', '키임', ['Lip'], 'Keyring-style lip products with accent details, popular with Gen Z.'),
    ('eiom', 'EIOM', '이옴', ['Mask Pack', 'Skincare', 'Body Care'], 'Trending at Olive Young.'),
    ('charde', 'Charde', '샤르드', ['Skincare', 'Eye', 'Sun Care', 'Patches', 'Makeup Base'], 'Trending at Olive Young.'),
    ('phytos', 'Phytos', '피토스', ['Hair Care'], ''),
    ('crebeau', 'crebeau', '끄레뷰', ['Skincare', 'Makeup Base', 'Mask Pack'], ''),
    ('lowlize', 'Lowlize', '로우라이즈', ['Skincare', 'Mask Pack', 'Sun Care'], 'Musinsa brand.'),
]
NMPA = {'phytos': 'All listed categories', 'crebeau': 'All listed categories', 'lowlize': 'Mask Pack'}

products, images, seen = [], {}, set()
for r in ROWS:
    bid, bname, bkr, _ = BRANDS[r['brand']]
    en, kr = tidy(r['name_en']), clean_kr(r['name_kr'], bid)
    if bid == 'tambeauty':
        en, kr = split_multi(r['name_en'])
    blob = (en + ' ' + kr).lower()
    if '단종' in blob or 'discontinued' in blob or 'to be discontinued' in (r.get('note') or '').lower():
        continue
    if bid == 'mixsoon' and 'diagnosis' in en.lower():
        continue
    en = re.sub(r'^\(단종\)\s*', '', en)
    vol = tidy(r['volume'])
    if not vol or vol in ('-',):
        m = VOL.search(en) or VOL.search(kr)
        vol = m.group(1) if m else ''
    if len(vol) > 60:
        vol = vol[:57] + '…'
    try:
        msrp = round(float(r['retail_usd']), 2) if r['retail_usd'] not in ('', None) else None
    except ValueError:
        msrp = None
    if msrp is not None and msrp <= 0:
        msrp = None
    key = (bid, en.lower(), kr, vol)
    if key in seen:
        continue
    seen.add(key)
    img = r['img']
    if img and img not in images:
        images[img] = 'data:image/webp;base64,' + base64.b64encode(open(f'build/thumbs2/{img}.webp', 'rb').read()).decode()
    products.append({'b': bid, 'c': category(r, en), 'l': tidy(HANGUL.sub('', r['category'])).title() if r['category'] else '',
                     'n': en or kr, 'k': kr if en else '', 'v': vol, 'p': msrp, 'i': img or ''})

brands = []
for full, (bid, bname, bkr, desc) in BRANDS.items():
    ps = [p for p in products if p['b'] == bid]
    cats = [c for c, _ in collections.Counter(p['c'] for p in ps).most_common()]
    brands.append({'id': bid, 'name': bname, 'kr': bkr, 'desc': desc, 'count': len(ps), 'cats': cats,
                   'note': RESTRICT.get(bid, ''), 'nmpa': ''})
for bid, bname, bkr, cats, desc in LIST_ONLY:
    brands.append({'id': bid, 'name': bname, 'kr': bkr, 'desc': desc, 'count': 0, 'cats': cats, 'note': '', 'nmpa': NMPA.get(bid, '')})
brands.sort(key=lambda b: b['name'].lower())

json.dump({'updated': '2026-11', 'brands': brands, 'products': products, 'images': images},
          open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
print('products', len(products), 'images', len(images), 'size KB', os.path.getsize(OUT) // 1024)
print(collections.Counter(p['c'] for p in products))
print('no msrp', sum(1 for p in products if p['p'] is None), 'no img', sum(1 for p in products if not p['i']))
