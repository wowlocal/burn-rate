#!/usr/bin/env python3
"""Copy the raw Codex art into the repository at half resolution (art/raw):
the model draws pixel art in blocks of about four pixels, so halving keeps
what the 0.2-0.25 scale processing uses, at a quarter of the size.
Usage: archive.py SOURCE_RAW_DIR  (default $BURNRATE_RAW, the full-size Codex outputs)"""
import os, sys
from pathlib import Path
from PIL import Image
if len(sys.argv) < 2 and "BURNRATE_RAW" not in os.environ:
    sys.exit("usage: archive.py SOURCE_RAW_DIR (or set BURNRATE_RAW)")
src = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ["BURNRATE_RAW"])
dst = Path(__file__).resolve().parents[2] / "art" / "raw"
for f in sorted(src.rglob("*.png")):
    rel = f.relative_to(src)
    if rel.parts[0] == "probe": continue
    out = dst / rel; out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(f).convert("RGB")
    img.resize((img.width // 2, img.height // 2), Image.BOX).save(out, optimize=True)
    for extra in (".prompt.txt",):
        p = f.with_name(f.stem + extra)
        if p.exists(): (out.parent / p.name).write_text(p.read_text())
print("archived to", dst)
