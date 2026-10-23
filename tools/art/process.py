#!/usr/bin/env python3
"""Turn Codex's magenta-backed pose sheets into game cells.

For one character: finds the poses on each raw sheet (A, B, C) in reading
order, scales them all by one factor (the first idle pose becomes HEIGHT px
tall), removes the magenta fringe, and anchors each pose's feet at the cell's
(CENTER_X, BASELINE). Pure black is the engine's transparent colour, so every
sprite pixel is kept off (0,0,0). Writes the sheet, its mirror, the portrait
(head:, 120x120) and the HUD picture (small:, 40x45) as 24-bit BMPs.

Usage: process.py RAW_DIR STEM OUT_DIR [--tint HUE_DEGREES]
"""
import argparse, json, struct, sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

CELL = 109           # the DAT's w/h; the sheet pitch is CELL+1 (room for raised fists and thrown props)
COLUMNS, ROWS = 10, 4  # 40 pictures per sheet
CENTER_X, BASELINE = 49, 104
HEIGHT = 66          # default idle pose height in game pixels (characters.json "height" overrides)
POSES = {"A": 12, "B": 12, "C": 8}

def magenta(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return (r > 200) & (b > 200) & (g < 90) & (abs(r - b) < 60)

def dilate(mask, pad):
    out = mask.copy()
    for dy in range(-pad, pad + 1):
        for dx in range(-pad, pad + 1):
            out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out

def find_poses(img, expected, min_cells=150):
    a = np.asarray(img.convert("RGB")).astype(float); bg = magenta(a); fg = ~bg
    # The magenta fringe: only pixels next to the background are despilled,
    # so a character's own purples keep their colour.
    edge = fg & dilate(bg, 2)
    a[edge] = despill(a[edge][None])[0]
    # Group on a coarse grid (4 px), dilated so a pose's detached parts join;
    # the dilation shrinks until the expected number of poses separate.
    for pad in (3, 2, 1, 0, 4, 5):
        boxes = group(fg, pad, min_cells)
        if len(boxes) == expected: break
    tight = []
    for x0, y0, x1, y1 in boxes:
        ys, xs = np.nonzero(fg[y0:y1, x0:x1])
        tight.append((x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1))
    if len(tight) != expected:
        raise SystemExit(f"found {len(tight)} poses, expected {expected}: {tight}")
    return a, fg, order(tight)

def group(fg, pad, min_cells=150):
    s = 4; h, w = fg.shape; gh, gw = h // s, w // s
    grid = fg[:gh * s, :gw * s].reshape(gh, s, gw, s).any(axis=(1, 3))
    dil = np.zeros_like(grid)
    for dy in range(-pad, pad + 1):
        for dx in range(-pad, pad + 1):
            dil |= np.roll(np.roll(grid, dy, 0), dx, 1)
    seen = np.zeros_like(dil); boxes = []
    for y in range(gh):
        for x in range(gw):
            if dil[y, x] and not seen[y, x]:
                q = deque([(y, x)]); seen[y, x] = True; y0 = y1 = y; x0 = x1 = x; n = 0
                while q:
                    cy, cx = q.popleft(); n += grid[cy, cx]
                    y0, y1, x0, x1 = min(y0, cy), max(y1, cy), min(x0, cx), max(x1, cx)
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < gh and 0 <= nx < gw and dil[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
                if n > min_cells:
                    boxes.append([x0 * s, y0 * s, min(w, (x1 + 1) * s), min(h, (y1 + 1) * s)])
    return boxes

def order(tight):
    # Reading order: rows are poses whose vertical spans overlap.
    tight.sort(key=lambda b: (b[1] + b[3]) / 2)
    rows = []
    for b in tight:
        for row in rows:
            r0, r1 = min(x[1] for x in row), max(x[3] for x in row)
            if min(r1, b[3]) - max(r0, b[1]) > 0.35 * min(r1 - r0, b[3] - b[1]):
                row.append(b); break
        else:
            rows.append([b])
    return [b for row in rows for b in sorted(row, key=lambda b: b[0])]

def despill(rgb):
    r, g, b = (rgb[..., i].astype(float) for i in range(3))
    tint = np.minimum(r, b) - g
    over = np.clip(tint - 40, 0, None) * 0.85
    out = np.stack([r - over, g, b - over], axis=-1)
    return np.clip(out, 0, 255)

def render(a, fg, box, scale, tint=None):
    x0, y0, x1, y1 = box
    rgb = a[y0:y1, x0:x1].astype(float); m = fg[y0:y1, x0:x1].astype(float)
    w = max(1, round((x1 - x0) * scale)); h = max(1, round((y1 - y0) * scale))
    # Premultiplied resampling: colours come only from foreground pixels.
    pm = Image.fromarray(np.uint8(np.clip(rgb * m[..., None], 0, 255))).resize((w, h), Image.BOX)
    mm = Image.fromarray(np.uint8(m * 255)).resize((w, h), Image.BOX)
    pa = np.asarray(pm).astype(float); ma = np.asarray(mm).astype(float) / 255
    color = pa / np.maximum(ma[..., None], 1e-3)
    if tint is not None: color = hue_shift(color, tint)
    keep = ma > 0.5
    out = np.zeros((h, w, 3), np.uint8)
    out[keep] = np.clip(np.round(color[keep]), 0, 255).astype(np.uint8)
    black = keep & (out.sum(axis=-1) == 0)
    out[black] = (8, 8, 16)   # never the transparent key
    return out, keep

def hue_shift(rgb, degrees):
    img = Image.fromarray(np.uint8(np.clip(rgb, 0, 255))).convert("HSV")
    hsv = np.asarray(img).astype(int); hsv[..., 0] = (hsv[..., 0] + int(degrees / 360 * 255)) % 256
    return np.asarray(Image.fromarray(np.uint8(hsv), "HSV").convert("RGB")).astype(float)

def place(cell_rgb, keep, sprite_w):
    cell = np.zeros((CELL, CELL, 3), np.uint8)
    h, w = keep.shape
    ox = CENTER_X - w // 2; oy = BASELINE - h
    sx0, sy0 = max(0, -ox), max(0, -oy)
    dx0, dy0 = max(0, ox), max(0, oy)
    dx1, dy1 = min(CELL, ox + w), min(CELL, oy + h)
    if dx1 <= dx0 or dy1 <= dy0: return cell
    sub_keep = keep[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
    sub_rgb = cell_rgb[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
    region = cell[dy0:dy1, dx0:dx1]; region[sub_keep] = sub_rgb[sub_keep]
    return cell

def bmp_bytes(rgb):
    """24-bit BI_RGB BMP file bytes for an HxWx3 uint8 array: bfSize equal to
    the file size, reserved fields 0, pixels at 54, the exact image size."""
    h, w, _ = rgb.shape; stride = (w * 3 + 3) & ~3
    rows = bytearray()
    for y in range(h - 1, -1, -1):
        rows += np.ascontiguousarray(rgb[y, :, ::-1]).tobytes() + b"\0" * (stride - w * 3)
    info = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, len(rows), 2835, 2835, 0, 0)
    header = struct.pack("<2sIHHI", b"BM", 14 + len(info) + len(rows), 0, 0, 54)
    return header + info + bytes(rows)

def save_bmp(array, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(bmp_bytes(np.asarray(array, np.uint8)))

def main():
    p = argparse.ArgumentParser(); p.add_argument("raw"); p.add_argument("stem"); p.add_argument("out")
    p.add_argument("--tint", type=float, default=None); p.add_argument("--source-stem", default=None)
    p.add_argument("--height", type=float, default=HEIGHT)
    o = p.parse_args()
    src = o.source_stem or o.stem
    raw = Path(o.raw) / src; out = Path(o.out)
    sheets = {}
    for kind, count in POSES.items():
        f = raw / f"{src}_{kind}.png"
        if f.exists(): sheets[kind] = find_poses(Image.open(f), count)
    if "A" not in sheets: raise SystemExit(f"{raw}: no sheet A")
    a, fg, boxes = sheets["A"]
    scale = o.height / (boxes[0][3] - boxes[0][1])
    sheet = np.zeros((ROWS * (CELL + 1), COLUMNS * (CELL + 1), 3), np.uint8)
    report = {"scale": scale, "pictures": {}}
    index = 0
    for kind in ("A", "B", "C"):
        if kind not in sheets: index += POSES[kind]; continue
        a, fg, boxes = sheets[kind]
        for box in boxes:
            rgb, keep = render(a, fg, box, scale, o.tint)
            cell = place(rgb, keep, rgb.shape[1])
            r, c = divmod(index, COLUMNS)
            sheet[r * (CELL + 1):r * (CELL + 1) + CELL, c * (CELL + 1):c * (CELL + 1) + CELL] = cell
            report["pictures"][index] = {"sheet": kind, "size": [int(rgb.shape[1]), int(rgb.shape[0])]}
            index += 1
    save_bmp(sheet, out / f"{o.stem}_0.bmp")
    save_bmp(sheet[:, ::-1].copy(), out / f"{o.stem}_0_mirror.bmp")
    # Portrait and HUD picture: the portrait sheet if there is one, else the idle pose's head.
    portrait = raw / f"{src}_portrait.png"
    if portrait.exists():
        img = Image.open(portrait).convert("RGB"); pa = np.asarray(img); pf = ~magenta(pa)
        ys, xs = np.nonzero(pf); crop = img.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    else:
        a, fg, boxes = sheets["A"]; x0, y0, x1, y1 = boxes[0]
        side = int((y1 - y0) * 0.42); cx = (x0 + x1) // 2
        crop = Image.fromarray(np.uint8(np.clip(a, 0, 255))).crop((cx - side // 2 - side // 6, y0, cx + side // 2 - side // 6, y0 + side))
    face = np.asarray(crop.convert("RGB")).copy(); face[magenta(face)] = (40, 44, 70)
    if o.tint is not None: face = np.uint8(hue_shift(face, o.tint))
    def fit(img_array, w, h):
        img = Image.fromarray(np.uint8(img_array)); img.thumbnail((w, h), Image.LANCZOS)
        canvas = Image.new("RGB", (w, h), (40, 44, 70)); canvas.paste(img, ((w - img.width) // 2, h - img.height))
        arr = np.asarray(canvas).copy(); arr[arr.sum(axis=-1) == 0] = (8, 8, 16); return arr
    save_bmp(fit(face, 120, 120), out / f"{o.stem}_f.bmp")
    # The HUD picture: the face (the portrait's upper middle), not the bust.
    fh, fw = face.shape[:2]; cw = int(min(fw, fh) * 0.62); ch = min(fh, cw * 45 // 40)
    x0 = (fw - cw) // 2; y0 = int(fh * 0.04)
    save_bmp(fit(face[y0:y0 + ch, x0:x0 + cw], 40, 45), out / f"{o.stem}_s.bmp")
    (out / f"{o.stem}.json").write_text(json.dumps(report, indent=1))
    print(f"{o.stem}: {index} pictures, scale {scale:.3f}")

if __name__ == "__main__":
    main()
