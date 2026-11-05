"""Add buyer-facing navigation fields to data/catalog.json (idempotent).

Re-classifies every product from its names (English `n`, Korean `k`) with ordered
keyword rules, then writes:
  c  category : see CATS below (user-approved scheme, 2026-11-04)
  g  group    : Skincare | Makeup | Hair & Body | Sets & More
  groups / catOrder : display order for the site rail

Scheme (대표 지시, 2026-11-04):
  Skincare   : Serums & Ampoules / Masks & Patches / Toners, Pads & Mists /
               Creams & Essences / Sun Care / Cleansing
  Makeup     : Base / Lip / Eye / Cheek & Point
  Hair & Body: Hair Care / Body Care / Devices & Tools
  Sets & More: Sets & Kits / Other

Usage: python3 tools/enrich.py data/catalog.json [--report]
"""
import json, re, sys
from collections import Counter

GROUPS = ['Skincare', 'Makeup', 'Hair & Body', 'Sets & More']
CATS = [  # (category, group) in display order
    ('Serums & Ampoules', 'Skincare'),
    ('Masks & Patches', 'Skincare'),
    ('Toners, Pads & Mists', 'Skincare'),
    ('Creams & Essences', 'Skincare'),
    ('Sun Care', 'Skincare'),
    ('Cleansing', 'Skincare'),
    ('Base', 'Makeup'),
    ('Lip', 'Makeup'),
    ('Eye', 'Makeup'),
    ('Cheek & Point', 'Makeup'),
    ('Hair Care', 'Hair & Body'),
    ('Body Care', 'Hair & Body'),
    ('Devices & Tools', 'Hair & Body'),
    ('Sets & Kits', 'Sets & More'),
    ('Other', 'Sets & More'),
]
GROUP = dict(CATS)
DISCONTINUED = ['사용중지', '단종', 'DISCONTINUED']


def has(hay, *words):
    return any(w in hay for w in words)


def classify(p, brand_id):
    n = p['n'].lower()
    k = (p.get('k') or '').lower()
    hay = n + ' ' + k

    l = (p.get('l') or '').lower()

    # 1. Non-cosmetic extras
    if has(hay, 'mouthwash', 'wipe', 'eco pouch', 'eco bag', 'cotton pad', 'mist pump', 'tissue', '가글', '화장솜', '티슈'):
        return 'Other'
    # 2. Devices, device heads/cases, tools
    if has(hay, 'booster pro', 'v roller', 'ultra tune', 'focus shot', 'cleanser head', 'derma booster', 'brush', 'head case', 'velvet pouch', 'device', '브러쉬', '브러시', '디바이스'):
        return 'Devices & Tools'
    # 3. Lip (incl. lip balm / lip mask / lip serum; MIXSOON "Lip Balm" line)
    if has(hay, 'lip', '립') or 'lip' in l:
        return 'Lip'
    # 4. Bundles, trial kits, sample sachets (after Lip/Devices; "Shading Duo" is handled below)
    if not has(hay, 'shading', 'palette') and (re.search(r'\b(set|kit|duo)\b', n) or has(n, 'suit case', 'sachet', 'trial') or has(k, '세트', '키트', '샤쉐')):
        return 'Sets & Kits'
    # 5. Hair
    if brand_id == 'jennyhouse' or has(hay, 'shampoo', 'hair', 'scalp', 'conditioner', 'treatment', '샴푸', '헤어', '두피', '트리트먼트'):
        return 'Hair Care'
    # 6. Body (incl. hand, feminine/intimate, body peel)
    if has(hay, 'body', 'hand cream', 'hand wash', 'feminine', 'inner cleanser', 'homme cleanser', 'deodor', 'foot', '바디', '핸드', '청결제'):
        return 'Body Care'
    # 7. Masks & patches (before eye/cheek makeup: "eye patch", "cheek film"; before serum/cream: "ampoule mask")
    if has(hay, 'mask', 'patch', 'sheet', 'film', 'modeling', 'clay', ' pack', '마스크', '패치', '팩', '필름') or has(l, 'mask', 'patch', 'sheet'):
        return 'Masks & Patches'
    # 8. Makeup (before sun, since "Sun Flush" blush / "Sunset Veil" liner)
    if has(hay, 'eyeshadow', 'eye shadow', 'eye liner', 'eyeliner', 'brow', 'mascara', 'lash', '아이섀도', '아이라이너', '브로우', '마스카라'):
        return 'Eye'
    if has(hay, 'blush', 'highlighter', 'shading', 'contour', 'cheeky', 'cheek', 'color balm', '블러셔', '하이라이터', '쉐이딩', '치크'):
        return 'Cheek & Point'
    if has(hay, 'cushion', 'foundation', 'concealer', 'primer', 'powder balm', '쿠션', '파운데이션', '컨실러', '프라이머'):
        return 'Base'
    # 9. Sun
    if re.search(r'\bsun\b|sunscreen|suncream|sunstick|sunpod|sunshield|sunsheild|\bspf\b|\buv\b', n) or has(k, '선크림', '선스틱', '선세럼', '선스크린', '선쉴드', '선팟'):
        return 'Sun Care'
    # 10. Toners, pads, mists (explicit forms win over "serum"/"essence" in the name)
    if has(hay, 'toner', 'mist', 'spray', 'essence water', 'skin conditioning', '토너', '미스트', '스프레이') and not has(hay, 'cleanser', '클렌저'):
        return 'Toners, Pads & Mists'
    # 11. Cleansing (incl. peel pads, peeling gels, cleansing pads/powders)
    if has(hay, 'cleans', 'foam', 'wash', 'peel', 'exfoliat', 'micellar', 'remover', 'soap', 'rice bar', '클렌', '필링', '각질'):
        return 'Cleansing'
    if has(hay, 'pad', '패드'):
        return 'Toners, Pads & Mists'
    # 12. Creams (English name says cream/lotion/moisturizer) before serum keywords
    if has(n, 'cream', 'lotion', 'moisturizer', 'moisturizing milk', 'conditioning milk', 'emulsion') or has(k, '크림', '로션'):
        if not has(n, 'serum'):
            return 'Creams & Essences'
    # 13. Serums, ampoules, boosters, facial oils, mix-in powders
    if has(hay, 'serum', 'ampoule', 'ampule', 'seum', 'shot', 'booster', 'oil', 'spicule', 'powder', '세럼', '앰플', '오일', '파우더'):
        return 'Serums & Ampoules'
    # 14. Everything else in the cream/essence family
    if has(hay, 'cream', 'lotion', 'moistur', 'balm', 'gel', 'essence', 'milk', 'jelly', '크림', '에센스', '밤', '젤', '로션', '밀크'):
        return 'Creams & Essences'
    return 'Other'


def main(path, report=False):
    d = json.load(open(path, encoding='utf-8'))
    before = len(d['products'])
    d['products'] = [p for p in d['products'] if not any(f in (p['n'] + ' ' + (p.get('k') or '')) for f in DISCONTINUED)]
    if len(d['products']) != before:
        print('dropped discontinued:', before - len(d['products']))
    for b in d['brands']:
        b['count'] = sum(1 for p in d['products'] if p['b'] == b['id']) or b.get('count', 0) if b.get('count') else 0
    changes = []
    for p in d['products']:
        old = p.get('c')
        p['c'] = classify(p, p['b'])
        p['g'] = GROUP[p['c']]
        if report and old != p['c']:
            changes.append((old, p['c'], p['b'], p['n'][:60], (p.get('k') or '')[:24]))
    d['groups'] = GROUPS
    d['catOrder'] = [c for c, _ in CATS]
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(Counter(p['g'] for p in d['products']))
    for c, g in CATS:
        print(f'  {g:12s} {c:22s} {sum(1 for p in d["products"] if p["c"] == c)}')
    if report:
        print(f'\nchanged: {len(changes)}')
        for old, new, b, n, k in sorted(changes, key=lambda x: (x[0] or '', x[1])):
            print(f'  {str(old):22s} -> {new:22s} | {b:14s} | {n} | {k}')


if __name__ == '__main__':
    main(sys.argv[1], report='--report' in sys.argv)
