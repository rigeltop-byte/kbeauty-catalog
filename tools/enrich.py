"""Add buyer-facing navigation fields to data/catalog.json (idempotent).

Per product:
  g  group   : Skincare | Makeup | Hair & Body | Devices & Tools | Sets & More
  c  category: finer category (Makeup is split into Lip / Eye & Brow / Face & Cheek,
               'Other' powders become 'Powders & Boosters')
Usage: python3 tools/enrich.py data/catalog.json
"""
import json, sys

GROUP = {
    'Cleansing': 'Skincare', 'Toners, Pads & Mists': 'Skincare', 'Serums & Ampoules': 'Skincare',
    'Creams & Moisturizers': 'Skincare', 'Masks & Patches': 'Skincare', 'Sun Care': 'Skincare',
    'Powders & Boosters': 'Skincare',
    'Lip': 'Makeup', 'Eye & Brow': 'Makeup', 'Face & Cheek': 'Makeup',
    'Hair Care': 'Hair & Body', 'Body & Hand': 'Hair & Body',
    'Devices & Tools': 'Devices & Tools',
    'Sets & Kits': 'Sets & More', 'Home & Lifestyle': 'Sets & More', 'Other': 'Sets & More',
}
DISCONTINUED = ['사용중지', '단종', 'DISCONTINUED']
MAKEUP = [
    ('Lip', ['lip']),
    ('Eye & Brow', ['eyeshadow', 'eye shadow', 'eye liner', 'eyeliner', 'brow', 'mascara', 'lash']),
    ('Face & Cheek', ['cushion', 'foundation', 'concealer', 'blush', 'highlighter', 'shading', 'contour', 'powder', 'primer', 'cheek', 'balm']),
]

def refine(p):
    n = (p['n'] + ' ' + p.get('l', '')).lower()
    c = p['c']
    if c == 'Makeup':
        if 'veil calming mask' in n: c = 'Masks & Patches'
        else:
            c = next((name for name, keys in MAKEUP if any(k in n for k in keys)), 'Face & Cheek')
    elif c == 'Other' and 'powder' in n:
        c = 'Powders & Boosters'
    return c

def main(path):
    d = json.load(open(path, encoding='utf-8'))
    # discontinued items never reach buyers
    before = len(d['products'])
    d['products'] = [p for p in d['products'] if not any(f in (p['n'] + ' ' + (p.get('k') or '')) for f in DISCONTINUED)]
    if len(d['products']) != before: print('dropped discontinued:', before - len(d['products']))
    for b in d['brands']:
        b['count'] = sum(1 for p in d['products'] if p['b'] == b['id']) or b.get('count', 0) if b.get('count') else 0
    for p in d['products']:
        p['c'] = refine(p)
        p['g'] = GROUP.get(p['c'], 'Sets & More')
    d['groups'] = ['Skincare', 'Makeup', 'Hair & Body', 'Devices & Tools', 'Sets & More']
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    from collections import Counter
    print(Counter(p['g'] for p in d['products']))
    print(Counter((p['g'], p['c']) for p in d['products']))

if __name__ == '__main__':
    main(sys.argv[1])
