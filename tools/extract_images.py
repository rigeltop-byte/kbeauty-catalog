"""Map product images in the price workbooks to (sheet name, 1-based row).
Handles both in-cell pictures (richData) and floating drawing pictures.
Output: JSON {file: {sheet: {row: media_path}}}"""
import zipfile, re, json, sys, posixpath
import xml.etree.ElementTree as ET

NS = {
    'm': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'pr': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'rd': 'http://schemas.microsoft.com/office/spreadsheetml/2017/richdata',
    'rvr': 'http://schemas.microsoft.com/office/spreadsheetml/2022/richvaluerel',
    'xlrd': 'http://schemas.microsoft.com/office/spreadsheetml/2017/richdata',
}
RID = '{%s}id' % NS['r']
REMBED = '{%s}embed' % NS['r']


def rels(z, path):
    d = posixpath.dirname(path)
    rp = posixpath.join(d, '_rels', posixpath.basename(path) + '.rels')
    if rp not in z.namelist():
        return {}
    out = {}
    for rel in ET.fromstring(z.read(rp)).findall('pr:Relationship', NS):
        out[rel.get('Id')] = posixpath.normpath(posixpath.join(d, rel.get('Target')))
    return out


def col_to_idx(ref):
    letters = re.match(r'[A-Z]+', ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def extract(path):
    z = zipfile.ZipFile(path)
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    wbrels = rels(z, 'xl/workbook.xml')
    # rich value chain: vm (1-based) -> valueMetadata bk -> rc v -> futureMetadata bk -> rvb i -> rv -> rel idx -> media
    vm_to_media = {}
    if 'xl/metadata.xml' in z.namelist() and 'xl/richData/rdrichvalue.xml' in z.namelist():
        md = ET.fromstring(z.read('xl/metadata.xml'))
        fut = []
        for fm in md.findall('m:futureMetadata', NS):
            if fm.get('name') == 'XLRICHVALUE':
                for bk in fm.findall('m:bk', NS):
                    rvb = bk.find('.//xlrd:rvb', NS)
                    fut.append(int(rvb.get('i')))
        vmeta = []
        vmd = md.find('m:valueMetadata', NS)
        if vmd is not None:
            for bk in vmd.findall('m:bk', NS):
                rc = bk.find('m:rc', NS)
                vmeta.append(int(rc.get('v')))
        rvs = []
        for rv in ET.fromstring(z.read('xl/richData/rdrichvalue.xml')).findall('rd:rv', NS):
            vals = [v.text for v in rv.findall('rd:v', NS)]
            rvs.append(int(vals[0]))
        relids = [e.get(RID) for e in ET.fromstring(z.read('xl/richData/richValueRel.xml'))]
        rr = rels(z, 'xl/richData/richValueRel.xml')
        for i, fidx in enumerate(vmeta):
            try:
                rvi = fut[fidx]
                media = rr[relids[rvs[rvi]]]
                vm_to_media[i + 1] = media
            except (IndexError, KeyError):
                pass

    result = {}
    for sh in wb.find('m:sheets', NS):
        name = sh.get('name')
        spath = wbrels[sh.get(RID)]
        rowmap = {}  # row -> (priority, media)
        # in-cell images
        sx = z.read(spath).decode('utf-8')
        for m in re.finditer(r'<c r="([A-Z]+)(\d+)"[^>]*?\svm="(\d+)"', sx):
            row, vm = int(m.group(2)), int(m.group(3))
            if vm in vm_to_media and row not in rowmap:
                rowmap[row] = vm_to_media[vm]
        # drawing images
        srels = rels(z, spath)
        for rid, target in srels.items():
            if '/drawings/' not in target:
                continue
            dx = ET.fromstring(z.read(target))
            drels = rels(z, target)
            for anc in list(dx):
                tag = anc.tag.split('}')[1]
                if tag not in ('twoCellAnchor', 'oneCellAnchor'):
                    continue
                blip = anc.find('.//a:blip', NS)
                if blip is None or blip.get(REMBED) not in drels:
                    continue
                media = drels[blip.get(REMBED)]
                fr = int(anc.find('xdr:from/xdr:row', NS).text)
                to_el = anc.find('xdr:to/xdr:row', NS)
                to = int(to_el.text) if to_el is not None else fr
                # if image barely enters the last row, don't count it
                to_off = anc.find('xdr:to/xdr:rowOff', NS)
                if to_el is not None and to > fr and to_off is not None and int(to_off.text) < 50000:
                    to -= 1
                for r0 in range(fr, to + 1):
                    rowmap.setdefault(r0 + 1, media)
        result[name] = rowmap
    return result


if __name__ == '__main__':
    out = {}
    for p in sys.argv[2:]:
        res = extract(p)
        out[p] = {s: {str(k): v for k, v in m.items()} for s, m in res.items()}
        for s, m in res.items():
            print(posixpath.basename(p), s, len(m), 'rows with images')
    json.dump(out, open(sys.argv[1], 'w'), ensure_ascii=False)
