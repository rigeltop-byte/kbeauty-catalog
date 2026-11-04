"""Product thumbnails, 480px square on white, webp (hybrid background handling).

  white-uniform bg  -> trim only (robust bbox; nothing removed, pack graphics survive)
  other uniform bg  -> macOS Vision cutout when it covers the product extent, else tight colour-key flood (tol 16)
  photo bg          -> Vision cutout; fallback tight flood; fallback keep on a bg-coloured canvas

Vision cutouts come from tools/cutout.swift (compile: swiftc -O -o cutout tools/cutout.swift; run: ./cutout <cut_dir> <orig>...).
Usage: python3 tools/make_thumbs.py --orig build/orig --cut build/cut --out build/thumbs [--review build/review]
tools/thumb_overrides.json lists image keys that must use 'safe' (trim only): the cutout cut those products.
Originals are named <imagekey>.<ext>; the image key is md5(file bytes)[:12], the same key catalog.json uses.
"""
import argparse, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE, PAD, WORK = 480, 0.08, 520

def to_rgb(im):
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA'); bg = Image.new('RGB', im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[-1]); return bg
    return im.convert('RGB')

def shrink(im):
    sc = min(1.0, WORK / max(im.size))
    return im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS) if sc < 1 else im

def border_stats(a):
    h, w, _ = a.shape; r = max(2, int(min(h, w) * 0.03))
    ring = np.concatenate([a[:r].reshape(-1, 3), a[-r:].reshape(-1, 3), a[:, :r].reshape(-1, 3), a[:, -r:].reshape(-1, 3)])
    bg = np.median(ring, axis=0)
    return bg, (np.abs(ring - bg).max(axis=1) <= 28).mean()

def robust_bbox(mask):
    """bbox of a boolean mask ignoring specks: erode 5px, then row/col projection threshold."""
    if not mask.any(): return None
    er = np.asarray(Image.fromarray((mask.astype(np.uint8) * 255)).filter(ImageFilter.MinFilter(5))) > 0
    m2 = er if er.any() else mask
    h, w = m2.shape; tr = max(2, int(0.006 * w)); tc = max(2, int(0.006 * h))
    rows = np.where(m2.sum(axis=1) >= tr)[0]; cols = np.where(m2.sum(axis=0) >= tc)[0]
    if len(rows) == 0 or len(cols) == 0:
        rows = np.where(m2.any(axis=1))[0]; cols = np.where(m2.any(axis=0))[0]
    pad = 4
    return (max(0, cols[0] - pad), max(0, rows[0] - pad), min(w, cols[-1] + 1 + pad), min(h, rows[-1] + 1 + pad))

def flood_alpha(a, bg, tol=16):
    h, w, _ = a.shape
    diff = np.abs(a - bg).max(axis=2)
    m = Image.fromarray(((diff <= tol).astype(np.uint8) * 255)).copy()  # writable copy: floodfill silently no-ops on read-only buffers
    px = m.load()
    for x, y in [(x, y) for y in (0, h - 1) for x in range(0, w, 2)] + [(x, y) for x in (0, w - 1) for y in range(0, h, 2)]:
        if px[x, y] == 255: ImageDraw.floodfill(m, (x, y), 128)
    bgmask = np.array(m) == 128
    alpha = np.where(bgmask, 0, 255).astype(np.float32)
    ramp = np.clip((diff - tol * 0.6) / (tol * 0.8), 0, 1) * 255
    return np.where(bgmask, np.minimum(alpha, ramp), alpha).astype(np.uint8)

def place(img, bbox, canvas=(255, 255, 255)):
    im = img.convert('RGBA')
    if bbox: im = im.crop(bbox)
    inner = int(SIZE * (1 - 2 * PAD)); sc = min(inner / im.width, inner / im.height, 2.5)
    nw, nh = max(1, int(im.width * sc)), max(1, int(im.height * sc))
    im = im.resize((nw, nh), Image.LANCZOS)
    c = Image.new('RGBA', (SIZE, SIZE), tuple(int(v) for v in canvas) + (255,))
    c.alpha_composite(im, ((SIZE - nw) // 2, (SIZE - nh) // 2))
    return c.convert('RGB')

def area(b): return (b[2] - b[0]) * (b[3] - b[1]) if b else 0

def safe_bbox(mask):
    """bbox that never cuts the product: 3px speck erosion only, no projection threshold."""
    if not mask.any(): return None
    er = np.asarray(Image.fromarray((mask.astype(np.uint8) * 255)).filter(ImageFilter.MinFilter(3))) > 0
    m = er if er.any() else mask
    rows = np.where(m.any(axis=1))[0]; cols = np.where(m.any(axis=0))[0]; h, w = m.shape; pad = 5
    return (max(0, cols[0] - pad), max(0, rows[0] - pad), min(w, cols[-1] + 1 + pad), min(h, rows[-1] + 1 + pad))

def thumb(orig_path, cut_path=None, mode=None):
    """Return (PIL RGB 480x480, method). mode='safe' = trim only, nothing removed (for images the cutout would cut)."""
    im = shrink(to_rgb(Image.open(orig_path)))
    a = np.asarray(im).astype(np.int16)
    bg, uni = border_stats(a)
    if mode == 'safe':
        canvas = (255, 255, 255) if bg.min() >= 238 else bg
        return place(im, safe_bbox(np.abs(a - bg).max(axis=2) > 24), canvas), 'safe'
    dbox = robust_bbox(np.abs(a - bg).max(axis=2) > 24)
    vis = None
    if cut_path and os.path.exists(cut_path):
        c = Image.open(cut_path).convert('RGBA')
        if c.size != im.size: c = c.resize(im.size, Image.LANCZOS)
        vis = (c, robust_bbox(np.asarray(c)[:, :, 3] > 100))
    if uni >= 0.9 and bg.min() >= 238:
        return place(im, dbox), 'trim'
    if uni >= 0.85:
        if vis and vis[1] and area(vis[1]) >= 0.55 * area(dbox):
            return place(vis[0], vis[1]), 'vision'
        alpha = flood_alpha(a, bg); rgba = im.convert('RGBA'); rgba.putalpha(Image.fromarray(alpha))
        return place(rgba, robust_bbox(alpha > 100)), 'flood'
    if vis and vis[1] and area(vis[1]) >= 0.08 * im.width * im.height:
        return place(vis[0], vis[1]), 'vision'
    if uni >= 0.7:
        alpha = flood_alpha(a, bg); rgba = im.convert('RGBA'); rgba.putalpha(Image.fromarray(alpha))
        return place(rgba, robust_bbox(alpha > 100)), 'flood2'
    return place(im, dbox, bg), 'keep'

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--orig', required=True); ap.add_argument('--cut', default=None)
    ap.add_argument('--out', required=True); ap.add_argument('--review', default=None)
    ap.add_argument('--overrides', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'thumb_overrides.json'), help='JSON {imagekey: "safe"}')
    a = ap.parse_args()
    ov = json.load(open(a.overrides)) if a.overrides and os.path.exists(a.overrides) else {}
    os.makedirs(a.out, exist_ok=True); method = {}
    for f in sorted(os.listdir(a.orig)):
        k = f.rsplit('.', 1)[0]
        out, method[k] = thumb(os.path.join(a.orig, f), os.path.join(a.cut, k + '.png') if a.cut else None, ov.get(k))
        out.save(os.path.join(a.out, k + '.webp'), 'WEBP', quality=74, method=6)
    from collections import Counter
    print(Counter(method.values()))
    if a.review:
        os.makedirs(a.review, exist_ok=True); json.dump(method, open(os.path.join(a.review, 'method.json'), 'w'))
        for m in set(method.values()):
            ks = [k for k, v in method.items() if v == m][:80]; cols = 10; rows = (len(ks) + cols - 1) // cols
            sh = Image.new('RGB', (cols * 160, max(1, rows) * 160), (235, 235, 235))
            for i, k in enumerate(ks):
                sh.paste(Image.open(os.path.join(a.out, k + '.webp')).convert('RGB').resize((156, 156)), ((i % cols) * 160 + 2, (i // cols) * 160 + 2))
            sh.save(os.path.join(a.review, f'sheet_{m}.jpg'), quality=80)

if __name__ == '__main__':
    main()
