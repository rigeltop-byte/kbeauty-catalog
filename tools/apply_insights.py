"""Merge handoff/review-insights/review_insights.json into data/catalog.json (idempotent).

What it writes (buyer-facing only):
  catalog["scales"]      scale definitions used on the site: {key: {type: "bipolar"|"level", label, left?, right?}}
  catalog["insUpdated"]  "YYYY-MM" of the insight data (shown as "Updated Nov 2026")
  product["ins"]         {kind, vol, sc: [[key, 1..5], ...], tl, loved: [..3], gtk, best, sum, note?}
  brand["heroIns"]       same shape plus n (hero product name), for brands without a product list

Matching: (brand, catalog_names[i]) against the product name `n`, exact first, then case/space-insensitive.
Names that match nothing are printed as WARNING and skipped.

Never copied: summary_kr, sentiment (internal review fields), and anything else not listed above.
Wording check: review-source names (banned_terms.json beside the insights file), star ratings and efficacy or
medicine-like wording stop the run before anything is written. Product names are not checked.

Usage: python3 -I tools/apply_insights.py --catalog data/catalog.json --insights handoff/review-insights/review_insights.json
       add --dry-run to check matching without writing.
"""
import argparse, difflib, json, os, re, sys

INTERNAL = ('summary_kr', 'sentiment')

# Section 1 of the insights README: no review-source names, no ratings, no efficacy or medicine-like wording.
# Describe how a product feels in use ("soothing, comforting feel"), not what it does to a skin condition.
BANNED = [
    ('rating', r'[★☆]|\bstars?\b|\b\d(\.\d)?\s*/\s*5\b|\d\s*점|\bout of 5\b'),
    ('efficacy or medicine-like wording', r'\bcure[sd]?\b|\btreat(s|ed|ing|ment|ments)?\b|\bheal(s|ed|ing)?\b|\brepair(s|ed|ing)?\b'
        r'|hair[- ]?loss|\bprescription|\bclinically\b|\bmedical|\btherap(y|ies|eutic)\b|clear(s|ing)?\s+(up\s+)?acne|\bacne\s+(care|control)'
        r'|\bredness\b|blackhead|post-blemish|anti-?inflammat|\bimprove(s|d|ment)?\b'),
]
# Names that must never appear (review sources) live in banned_terms.json next to the insights file, outside the public site.


def norm(s):
    return re.sub(r'\s+', ' ', s or '').strip().casefold()


def buyer_texts(e):
    out = [e.get('kind', ''), e.get('texture_line', ''), e.get('good_to_know', ''), e.get('best_for', ''), e.get('summary', ''), e.get('note', '')]
    return [t for t in out + list(e.get('loved_for') or []) if t]


def compact(e, scale_dict, problems, who):
    sc = []
    for s in e.get('scales') or []:
        k, v = s.get('key'), s.get('value')
        if k not in scale_dict:
            problems.append(f'{who}: scale "{k}" is not in scale_dictionary, skipped'); continue
        if not isinstance(v, int) or not 1 <= v <= 5:
            problems.append(f'{who}: scale "{k}" value {v!r} is not 1-5, skipped'); continue
        sc.append([k, v])
    o = {}
    if e.get('kind'): o['kind'] = e['kind']
    o['vol'] = e.get('review_volume', '')
    o['sc'] = sc
    o['tl'] = e.get('texture_line', '')
    o['loved'] = list(e.get('loved_for') or [])[:3]
    o['gtk'] = e.get('good_to_know', '')
    o['best'] = e.get('best_for', '')
    o['sum'] = e.get('summary', '')
    if e.get('note'): o['note'] = e['note']
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--catalog', required=True)
    ap.add_argument('--insights', required=True)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    d = json.load(open(a.catalog, encoding='utf-8'))
    src = json.load(open(a.insights, encoding='utf-8'))
    banned = list(BANNED)
    extra = os.path.join(os.path.dirname(os.path.abspath(a.insights)), 'banned_terms.json')
    if os.path.exists(extra):
        banned += [tuple(x) for x in json.load(open(extra, encoding='utf-8')).get('patterns', [])]
    else:
        print('note: banned_terms.json not found next to the insights file; source-name check skipped')
    scale_dict = src.get('scale_dictionary') or {}
    entries, heroes = src.get('products') or [], src.get('brand_heroes') or []

    # 1) wording check before touching the catalog
    hits = []
    for e in entries + heroes:
        who = e.get('brand', '?') + ' / ' + (e.get('hero_product') or (e.get('catalog_names') or ['?'])[0])
        for t in buyer_texts(e):
            for label, pat in banned:
                m = re.search(pat, t, re.I)
                if m: hits.append(f'{who}: {label} "{m.group(0)}" in: {t}')
    if hits:
        print('ERROR: wording that must not go on the site. Fix review_insights.json and run again.')
        for h in hits: print('  -', h)
        sys.exit(2)

    # 2) start clean so removed entries do not linger
    for p in d['products']: p.pop('ins', None)
    for b in d['brands']: b.pop('heroIns', None)

    brand_ids = {b['id'] for b in d['brands']}
    exact, loose, names_by_brand = {}, {}, {}
    for i, p in enumerate(d['products']):
        exact.setdefault((p['b'], p['n']), []).append(i)
        loose.setdefault((p['b'], norm(p['n'])), []).append(i)
        names_by_brand.setdefault(p['b'], []).append(p['n'])

    warnings, used_scales = [], set()
    matched_entries, sku_idx = 0, set()
    for e in entries:
        br = e.get('brand')
        who = f'{br} / {e.get("kind", "")}'
        if br not in brand_ids:
            warnings.append(f'brand "{br}" is not in the catalog ({len(e.get("catalog_names") or [])} names skipped)'); continue
        ins = compact(e, scale_dict, warnings, who)
        hit = False
        for name in dict.fromkeys(e.get('catalog_names') or []):  # de-duplicate, keep order
            idxs = exact.get((br, name))
            if not idxs:
                idxs = loose.get((br, norm(name)))
                if idxs: print(f'note: matched ignoring case/spaces: [{br}] {name}')
            if not idxs:
                near = difflib.get_close_matches(name, names_by_brand.get(br, []), n=2, cutoff=0.6)
                warnings.append(f'no catalog product named [{br}] "{name}"' + (f' (closest: {near})' if near else ''))
                continue
            for i in idxs:
                if 'ins' in d['products'][i]:
                    warnings.append(f'[{br}] "{name}" is listed in two insight entries, the later one wins')
                d['products'][i]['ins'] = ins
                sku_idx.add(i)
            hit = True
        if hit:
            matched_entries += 1
            used_scales.update(k for k, _ in ins['sc'])

    by_brand = {b['id']: b for b in d['brands']}
    hero_done = 0
    for h in heroes:
        b = by_brand.get(h.get('brand'))
        if not b:
            warnings.append(f'hero brand "{h.get("brand")}" is not in the catalog'); continue
        ins = compact(h, scale_dict, warnings, f'{b["id"]} / hero')
        ins = {'n': h.get('hero_product', ''), **ins}
        b['heroIns'] = ins
        used_scales.update(k for k, _ in ins['sc'])
        hero_done += 1

    d['scales'] = {k: {f: v[f] for f in ('type', 'label', 'left', 'right') if f in v} for k, v in scale_dict.items() if k in used_scales}
    d['insUpdated'] = (src.get('version') or '')[:7]

    # 3) report
    for w in warnings: print('WARNING:', w)
    print(f'insight entries matched: {matched_entries}/{len(entries)}, SKUs with insight: {len(sku_idx)}, brand heroes merged: {hero_done}/{len(heroes)}, scales used: {len(d["scales"])}')
    blob = json.dumps([p.get('ins') for p in d['products']] + [b.get('heroIns') for b in d['brands']], ensure_ascii=False)
    leak = [k for k in INTERNAL if k in blob]
    print('internal fields leaked:', leak or 'none')
    if leak: sys.exit(3)

    if a.dry_run:
        print('dry run: catalog not written'); return
    json.dump(d, open(a.catalog, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'catalog written: {os.path.getsize(a.catalog) / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
