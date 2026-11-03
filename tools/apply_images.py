"""Write thumbnails into data/catalog.json, fill image gaps, and add navigation groups.

  --thumbs  dir of <imagekey>.webp (from make_thumbs.py) -> replaces every image in catalog.json
  --extra   dir of extra product photos (official brand shots) named <anything>.jpg with a map file
            extra.json: {"file.jpg": {"b": "<brandId>", "match": "<substring of product n, upper>"}}
            each is run through make_thumbs.thumb and keyed by md5(file)[:12]
  Products still without an image borrow the image of the closest same-brand sibling (other size/scent)
  when the name similarity is >= 0.78; those get "ir": 1 (representative image) so the UI can say so.
  Finally enrich.py adds group/category fields.
Usage: python3 tools/apply_images.py --catalog data/catalog.json --thumbs build/thumbs [--extra build/extra]
"""
import argparse, base64, hashlib, json, os, re, sys
from difflib import SequenceMatcher
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_thumbs, enrich

def data_uri(path):
    return 'data:image/webp;base64,' + base64.b64encode(open(path, 'rb').read()).decode()

def norm(n):
    n = n.lower(); n = re.sub(r'\d+\s*(ml|g|ea|pcs|pads|pad|oz|fl\.?\s*oz|x\s*\d+ea|\*\s*\d+)', ' ', n)
    n = re.sub(r'[\(\)\[\]/\-\*,.]', ' ', n); return re.sub(r'\s+', ' ', n).strip()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--catalog', required=True); ap.add_argument('--thumbs', required=True)
    ap.add_argument('--extra', default=None); a = ap.parse_args()
    d = json.load(open(a.catalog, encoding='utf-8'))
    prods = d['products']
    images = {}
    for k in d['images']:
        p = os.path.join(a.thumbs, k + '.webp')
        if os.path.exists(p): images[k] = data_uri(p)
    print('thumbnails replaced:', len(images), 'of', len(d['images']))
    # extra official photos
    if a.extra and os.path.exists(os.path.join(a.extra, 'extra.json')):
        emap = json.load(open(os.path.join(a.extra, 'extra.json')))
        for f, spec in emap.items():
            src = os.path.join(a.extra, f); raw = open(src, 'rb').read(); k = hashlib.md5(raw).hexdigest()[:12]
            out, m = make_thumbs.thumb(src); tmp = os.path.join(a.thumbs, k + '.webp'); out.save(tmp, 'WEBP', quality=74, method=6)
            images[k] = data_uri(tmp)
            hit = [p for p in prods if p['b'] == spec['b'] and spec['match'].upper() in p['n'].upper()]
            for p in hit: p['i'] = k; p.pop('ir', None)
            print(f'extra {f} -> {k} ({m}) -> {len(hit)} product(s):', [p['n'] for p in hit])
    # siblings for the rest
    have = [p for p in prods if p.get('i') in images]
    for p in prods:
        if p.get('i') in images: continue
        cands = [(SequenceMatcher(None, norm(p['n']), norm(h['n'])).ratio(), h) for h in have if h['b'] == p['b']]
        if not cands: continue
        r, h = max(cands, key=lambda x: x[0])
        if r >= 0.78:
            p['i'] = h['i']; p['ir'] = 1; print(f'sibling {r:.2f}: {p["n"]}  <=  {h["n"]}')
        else:
            print(f'NO IMAGE ({r:.2f}): {p["b"]} | {p["n"]}')
    d['images'] = images
    json.dump(d, open(a.catalog, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    enrich.main(a.catalog)
    miss = [p for p in prods if p.get('i') not in images]
    print('products without image:', len(miss), '| catalog size MB: %.2f' % (os.path.getsize(a.catalog) / 1e6))

if __name__ == '__main__':
    main()
