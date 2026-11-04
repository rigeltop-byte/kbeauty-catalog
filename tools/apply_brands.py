"""Merge handoff/brand-highlights/brand_highlights.json into data/catalog.json brands (idempotent).

Buyer-facing fields added per brand:
  thumb      image key in catalog images (existing product thumbnail key, or the brand thumb embedded as data URI)
  tagline    one line (tagline_en)
  desc       replaced by desc_en when present
  strengths  up to 3 lines (strengths_en)
  heroes     [{n, note}] from hero_products (en, point_en)
  focus      category_focus
Internal review fields (*_kr, confidence, image_status, image_note, thumb_source) are NOT copied.
Usage: python3 tools/apply_brands.py --catalog data/catalog.json --highlights handoff/brand-highlights
"""
import argparse, base64, hashlib, json, os, re

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--catalog', required=True); ap.add_argument('--highlights', required=True); a = ap.parse_args()
    d = json.load(open(a.catalog, encoding='utf-8'))
    h = json.load(open(os.path.join(a.highlights, 'brand_highlights.json'), encoding='utf-8'))
    items = h['brands'] if isinstance(h, dict) and 'brands' in h else h
    if isinstance(items, dict): items = list(items.values())
    by = {b['id']: b for b in items}
    done, embedded = 0, 0
    for b in d['brands']:
        s = by.get(b['id'])
        if not s: print('no highlight for', b['id']); continue
        m = re.search(r'catalog image key ([0-9a-f]{12})', s.get('thumb_source', '') or '')
        if m and m.group(1) in d['images']:
            b['thumb'] = m.group(1)
        else:
            p = os.path.join(a.highlights, s['thumb']); raw = open(p, 'rb').read(); k = hashlib.md5(raw).hexdigest()[:12]
            if k not in d['images']:
                d['images'][k] = 'data:image/webp;base64,' + base64.b64encode(raw).decode(); embedded += 1
            b['thumb'] = k
        if s.get('tagline_en'): b['tagline'] = s['tagline_en']
        if s.get('desc_en'): b['desc'] = s['desc_en']
        if s.get('strengths_en'): b['strengths'] = s['strengths_en'][:3]
        if s.get('hero_products'): b['heroes'] = [{'n': x['en'], 'note': x.get('point_en', '')} for x in s['hero_products'][:3]]
        if s.get('category_focus'): b['focus'] = s['category_focus']
        done += 1
    json.dump(d, open(a.catalog, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'brands merged: {done}, brand thumbs embedded: {embedded}, catalog MB: {os.path.getsize(a.catalog)/1e6:.2f}')
    leak = [k for b in d['brands'] for k in b if k.endswith('_kr') or k in ('confidence', 'image_status', 'image_note', 'thumb_source')]
    print('internal fields leaked:', leak or 'none')

if __name__ == '__main__':
    main()
