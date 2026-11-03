"""Square, evenly padded product thumbnails on white (same hash names as before)."""
import json, zipfile, io, hashlib, os
from PIL import Image, ImageChops, ImageStat

m = json.load(open('build/imgmap.json'))
rows = json.load(open('build/rows_img.json'))
need = {r['img'] for r in rows if r['img']}
os.makedirs('build/thumbs2', exist_ok=True)
SIZE, PAD = 480, 0.08
done = set()
for f, sheets in m.items():
    z = zipfile.ZipFile(f)
    for sheet, rmap in sheets.items():
        for media in set(rmap.values()):
            data = z.read(media)
            h = hashlib.md5(data).hexdigest()[:12]
            if h not in need or h in done:
                continue
            try:
                im = Image.open(io.BytesIO(data)); im.load()
            except Exception:
                continue
            if im.mode in ('RGBA', 'LA', 'P'):
                im = im.convert('RGBA'); bg = Image.new('RGB', im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[-1]); im = bg
            else:
                im = im.convert('RGB')
            # background = median of the four corners; trim it away
            w, hgt = im.size
            corners = [im.getpixel((0, 0)), im.getpixel((w - 1, 0)), im.getpixel((0, hgt - 1)), im.getpixel((w - 1, hgt - 1))]
            bgc = tuple(sorted(c[i] for c in corners)[1] for i in range(3))
            diff = ImageChops.difference(im, Image.new('RGB', im.size, bgc))
            bbox = ImageChops.add(diff, diff, 2.0, -24).getbbox()
            if bbox:
                im = im.crop(bbox)
            # light, near-uniform backgrounds get replaced by white canvas; darker photo backgrounds keep a matching canvas
            light = sum(bgc) / 3 > 225
            canvas_color = (255, 255, 255) if light else bgc
            inner = int(SIZE * (1 - 2 * PAD))
            scale = min(inner / im.width, inner / im.height, 2.5)  # allow mild upscaling only
            nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
            im = im.resize((nw, nh), Image.LANCZOS)
            canvas = Image.new('RGB', (SIZE, SIZE), canvas_color)
            canvas.paste(im, ((SIZE - nw) // 2, (SIZE - nh) // 2))
            canvas.save(f'build/thumbs2/{h}.webp', 'WEBP', quality=74, method=6)
            done.add(h)
print('thumbs', len(done), 'of', len(need), 'KB', sum(os.path.getsize('build/thumbs2/' + x) for x in os.listdir('build/thumbs2')) // 1024)
