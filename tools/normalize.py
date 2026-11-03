import openpyxl, csv, sys, collections

F1 = '/mnt/user-data/uploads/발송용_화장품_제품_제안_price.xlsx'
F2 = '/mnt/user-data/uploads/메이저_화장품_브랜드_제안_price.xlsx'
OUT = sys.argv[1]

# sheet: (brand, start_row, cat, kr, en, vol, retail, supply, barcode)
MAP = {
    (F1, '제니하우스 hair_body '): ('JENNYHOUSE 제니하우스', 6, 2, 4, 5, 6, 7, 8, None),
    (F1, 'Franz'): ('FRANZ 프란츠', 5, 1, 3, 4, 5, 7, 8, 13),
    (F1, 'KUNDAL'): ('KUNDAL 쿤달', 7, 2, 5, 6, None, 10, 11, 4),
    (F1, '탐뷰티'): ('TAM BEAUTY 탐뷰티', 7, 1, None, 4, 5, 11, 12, 3),
    (F1, 'Kischcatch'): ('KITSCH CATCH 키치캐치', 5, None, 2, 3, 5, 6, 7, None),
    (F2, 'medicube'): ('medicube 메디큐브', 5, 7, 9, 10, 12, 19, 22, 5),
    (F2, 'MIXSOON'): ('MIXSOON 믹순', 7, 1, 2, 3, 7, 8, 9, 5),
    (F2, 'Dr.Althea'): ('Dr.Althea 닥터엘시아', 6, 1, 8, 9, 13, 10, 12, 3),
    (F2, '셀리맥스'): ('CELIMAX 셀리맥스', 7, 0, None, 3, 5, 4, 6, 2),
    (F2, 'Anua'): ('ANUA 아누아', 6, None, 2, 3, None, 5, 6, 0),
    (F2, '조선미녀'): ('Beauty of Joseon 조선미녀', 3, None, 4, 3, 6, 13, 14, 5),
}

def num(v):
    try:
        x = float(v)
        return round(x, 2)
    except (TypeError, ValueError):
        return None

def clean(v):
    if v is None:
        return ''
    s = str(v).replace('\n', ' ').replace('\t', ' ')
    return ' '.join(s.split())

rows_out = []
for f in (F1, F2):
    wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
    for ws in wb:
        key = (f, ws.title)
        if key not in MAP:
            print('UNMAPPED', ws.title); continue
        brand, start, c_cat, c_kr, c_en, c_vol, c_r, c_s, c_bc = MAP[key]
        cur_cat = ''
        for cells in ws.iter_rows():
            i = next((c.row for c in cells if getattr(c, 'row', None)), None)
            if i is None or i < start:
                continue
            r = [getattr(c, 'value', None) for c in cells]
            g = lambda c: r[c] if (c is not None and c < len(r)) else None
            if c_cat is not None and g(c_cat) not in (None, ''):
                cur_cat = clean(g(c_cat))
            kr, en = clean(g(c_kr)), clean(g(c_en))
            if ws.title == 'Kischcatch' and g(4):
                kr, en = kr + ' ' + clean(g(4)), en + ' ' + clean(g(4))
            sup = num(g(c_s))
            if not (kr or en) or sup is None:
                continue
            bc = g(c_bc)
            bc = clean(int(bc) if isinstance(bc, float) else bc)
            rows_out.append({
                'source': '발송용' if f == F1 else '메이저',
                'file': f, 'sheet': ws.title, 'row': i,
                'brand': brand, 'category': cur_cat, 'name_kr': kr, 'name_en': en,
                'volume': clean(g(c_vol)), 'retail_usd': num(g(c_r)) or '',
                'supply_usd': sup, 'barcode': bc,
            })

with open(OUT, 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()))
    w.writeheader(); w.writerows(rows_out)

c = collections.Counter(r['brand'] for r in rows_out)
for b, n in c.items():
    sups = [r['supply_usd'] for r in rows_out if r['brand'] == b]
    cats = collections.Counter(r['category'] for r in rows_out if r['brand'] == b)
    print(f'{b}: {n} SKU, supply {min(sups)}~{max(sups)} | cats: {list(cats)[:12]}')
print('TOTAL', len(rows_out))
