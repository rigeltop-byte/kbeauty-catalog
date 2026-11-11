"""Add buyer-facing navigation fields to data/catalog.json (idempotent).

Re-classifies every product from its names (English `n`, Korean `k`) with ordered
keyword rules, then writes:
  c  category : see CATS below (user-approved scheme, 2026-11-04)
  g  group    : Skincare | Makeup | Hair & Body | Sets & More
  groups / catOrder : display order for the site rail
  tg / ingredients  : key ingredients named in the product name (tg on products, [key, label] list at top level)

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


# Key ingredients, read from the product's own name only (no claims, no outside data).
# Makeup is skipped (shade names such as "Honey Apple"), and KUNDAL scent names after " - " are ignored.
INGREDIENTS = [
    ('pdrn', 'PDRN', r'pdrn|피디알엔'),
    ('cica', 'Centella / Cica', r'centella|cica|madeca|병풀|시카'),
    ('heartleaf', 'Heartleaf', r'heart?leaf|어성초'),
    ('hyaluronic', 'Hyaluronic acid', r'hyalur|히알루'),
    ('collagen', 'Collagen', r'collagen|콜라겐'),
    ('niacinamide', 'Niacinamide', r'niacin|나이아신'),
    ('peptide', 'Peptide', r'peptide|펩타이드'),
    ('vitc', 'Vitamin C', r'vita(min)?[ -]?c\b|vitac\b|비타\s?씨|비타민\s?c|비타c'),
    ('retinol', 'Retinol / Retinal', r'retino|retinal|레티놀|레티날'),
    ('ceramide', 'Ceramide', r'ceramide|세라마이드'),
    ('acids', 'AHA / BHA / PHA', r'\b(aha|bha|pha|lha)\b|ahabha|salicylic|succinic'),
    ('azelaic', 'Azelaic acid', r'azelaic|아젤라'),
    ('kojic', 'Kojic acid', r'kojic|코직'),
    ('turmeric', 'Turmeric', r'turmeric|터메릭'),
    ('txa', 'Tranexamic acid', r'\btxa\b|tranex|트라넥'),
    ('glutathione', 'Glutathione', r'glutathione|글루타치온'),
    ('exosome', 'Exosome', r'exosome|엑소좀'),
    ('egf', 'EGF', r'\begf\b'),
    ('stemcell', 'Stem cell culture', r'stem cell|줄기세포'),
    ('hypochlorous', 'Hypochlorous acid', r'hypochlor'),
    ('panthenol', 'Panthenol', r'panthenol|판테놀'),
    ('amino', 'Amino acid', r'amino|아미노'),
    ('soy', 'Soybean', r'soybean|soy ?milk|두유|콩|(?<!mung )(?<!red )\bbean\b'),
    ('rice', 'Rice', r'\brice\b|쌀|라이스'),
    ('ginseng', 'Ginseng', r'ginseng|인삼|홍삼'),
    ('bifida', 'Bifida', r'bifida|비피다'),
    ('galactomyces', 'Galactomyces', r'galactomyces|갈락토'),
    ('noni', 'Noni', r'\bnoni\b|노니'),
    ('peach', 'Peach', r'\bpeach\b|복숭아'),
    ('birch', 'Birch', r'birch|자작'),
    ('greentea', 'Green tea', r'green ?tea|녹차'),
    ('propolis', 'Propolis', r'propo?lis|프로폴리스'),
    ('snail', 'Snail mucin', r'snail|스네일'),
    ('mugwort', 'Mugwort', r'mugwort|쑥'),
    ('redbean', 'Red bean', r'red bean|붉은팥'),
    ('mungbean', 'Mung bean', r'mung bean|녹두'),
    ('lotus', 'Lotus', r'lotus|연꽃'),
    ('reishi', 'Reishi', r'reishi|영지'),
    ('hinoki', 'Hinoki', r'hinoki|편백'),
    ('betaglucan', 'Beta-glucan', r'glucan|글루칸'),
    ('honey', 'Honey', r'honey|허니'),
    ('macadamia', 'Macadamia', r'macadamia|마카다미아'),
    ('shea', 'Shea butter', r'shea|시어'),
    ('teatree', 'Tea tree', r'tea ?tree|티트리'),
    ('caffeine', 'Caffeine', r'caffeine|카페인'),
    ('rosemary', 'Rosemary', r'rosemary|로즈마리'),
]
_ING = [(k, lab, re.compile(pat, re.I)) for k, lab, pat in INGREDIENTS]


def ingredients(p, group):
    """Ingredient keys named in the product name. Returns [] for makeup and non-cosmetic items."""
    if group == 'Makeup' or p['c'] in ('Other', 'Devices & Tools'):
        return []
    n, k = p['n'], (p.get('k') or '')
    if p['b'] == 'kundal':  # "... 500ML - CHERRY BLOSSOM" / "...1구-체리블라썸": the tail is a scent
        n = n.split(' - ')[0]
        k = k.rsplit('-', 1)[0]
    hay = n + ' ' + k
    return [key for key, _, rx in _ING if rx.search(hay)]


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
        tg = ingredients(p, p['g'])
        if tg: p['tg'] = tg
        else: p.pop('tg', None)
        if report and old != p['c']:
            changes.append((old, p['c'], p['b'], p['n'][:60], (p.get('k') or '')[:24]))
    d['groups'] = GROUPS
    d['catOrder'] = [c for c, _ in CATS]
    ing_n = Counter(k for p in d['products'] for k in p.get('tg', []))
    d['ingredients'] = [[k, lab] for k, lab, _ in INGREDIENTS if ing_n[k]]
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(Counter(p['g'] for p in d['products']))
    for c, g in CATS:
        print(f'  {g:12s} {c:22s} {sum(1 for p in d["products"] if p["c"] == c)}')
    print('ingredient tags:', ', '.join(f'{lab} {ing_n[k]}' for k, lab, _ in INGREDIENTS if ing_n[k]))
    print('products with an ingredient tag:', sum(1 for p in d['products'] if p.get('tg')))
    if report:
        print(f'\nchanged: {len(changes)}')
        for old, new, b, n, k in sorted(changes, key=lambda x: (x[0] or '', x[1])):
            print(f'  {str(old):22s} -> {new:22s} | {b:14s} | {n} | {k}')


if __name__ == '__main__':
    main(sys.argv[1], report='--report' in sys.argv)
