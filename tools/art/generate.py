#!/usr/bin/env python3
"""Generate character art with Codex CLI's image generation.

Each call runs `codex exec` in the character's folder under $BURNRATE_RAW and
asks for one magenta-backed image. Sheet A is drawn from the description
alone; sheets B, C and the portrait take sheet A as their visual reference,
so the character stays the same. Raw outputs stay outside the repository.

Usage: generate.py STEM KIND [KIND...]   (KIND: A, B, C, portrait)
       generate.py --all KIND            (every character)
"""
import json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if "BURNRATE_RAW" not in os.environ:
    sys.exit("set BURNRATE_RAW to a folder outside the repository for the full-size Codex outputs")
RAW = Path(os.environ["BURNRATE_RAW"])
CHARACTERS = json.loads((ROOT / "art" / "characters.json").read_text())

STYLE = ("in the style of 1990s arcade beat-'em-up pixel art: crisp pixels, limited palette, dark navy "
         "(never pure black) 1-pixel outlines, compact proportions about 5 heads tall")
BACKGROUND = ("Background: one flat solid magenta (#FF00FF) colour everywhere, no gradients, no shadows, "
              "no floor, no text, no grid lines, no frames.")
SHEETS = {
    "A": ["idle stance, fists up", "idle stance, breathing variant", "walk step A", "walk step B", "walk step C",
          "walk step D", "run stride A, leaning forward", "run stride B", "run stride C", "punch wind-up",
          "punch fully extended", "high kick fully extended"],
    "B": ["crouch before a jump, knees bent", "jumping up, knees tucked", "airborne at the top of a jump",
          "airborne flying kick, leg extended forward and down", "low forward dash lunge",
          "guard block, forearms crossed in front of the face", "hit recoil A, head snapped back, wincing",
          "hit recoil B, doubled over, hand on stomach", "knocked off the feet flying backwards, body horizontal, airborne",
          "lying flat on the back on the ground, horizontal", "getting up from one knee", "landing crouch after a jump"],
}

def special_poses(c):
    return [f"signature move wind-up: {c['special_windup']}", f"signature move release: {c['special_release']}",
            "rising uppercut, fist high above the head", "running shoulder charge", "spinning back fist",
            "victory pose, triumphant", "exhausted, hands on knees", "taunt, pointing forward"]

def prompt(stem, kind):
    c = CHARACTERS[stem]
    who = f"The character (fictional, not a real person): {c['description']}"
    if kind in ("A", "B", "C"):
        poses = SHEETS[kind] if kind in SHEETS else special_poses(c)
        cols, rows = (4, 3) if len(poses) == 12 else (4, 2)
        listed = ", ".join(f"{i+1} {p}" for i, p in enumerate(poses))
        lead = ("Use your image generation tool to create ONE image" if kind == "A" else
                "The attached image is sprite sheet A of this character. Use your image generation tool, with the "
                "attached sheet as the visual reference, to create ONE new image. Keep EXACTLY the same character "
                "design, colours, pixel-art style, outline colour, scale and proportions as the reference.")
        return (f"{lead} Save it in the current directory as {stem}_{kind}.png (keep the tool's full resolution). "
                f"It is a sprite sheet for a 2D side-scrolling fighting game {STYLE}. {BACKGROUND} Layout: {cols} "
                f"columns x {rows} rows, {len(poses)} separate full-body poses with generous magenta space between "
                f"them, every pose at the same scale, every pose facing RIGHT. {who} Poses in reading order: {listed}. "
                f"Then print the saved file's absolute path and pixel size.")
    if kind == "portrait":
        return ("The attached image is sprite sheet A of this character. Use your image generation tool, with the "
                "attached sheet as the visual reference, to create ONE new image and save it in the current directory "
                f"as {stem}_portrait.png (full resolution): a head-and-shoulders portrait of the same character for a "
                f"fighting game's character select screen, facing slightly right, {STYLE}, same colours and design, "
                f"filling most of a square frame. {BACKGROUND} {who} Then print the saved file's absolute path and pixel size.")
    raise SystemExit(f"unknown kind {kind}")

def run(stem, kind):
    out = RAW / stem; out.mkdir(parents=True, exist_ok=True)
    target = out / f"{stem}_{kind}.png"
    if target.exists():
        print(f"{target} exists, skipped", flush=True); return True
    args = ["codex", "exec", "--skip-git-repo-check", "-C", str(out), "--sandbox", "workspace-write"]
    if kind != "A": args += ["-i", str(out / f"{stem}_A.png")]
    text = prompt(stem, kind)
    (out / f"{stem}_{kind}.prompt.txt").write_text(text + "\n")
    start = time.time()
    with open(out / f"{stem}_{kind}.log", "w") as log:
        code = subprocess.run(args, input=text, text=True, stdout=log, stderr=subprocess.STDOUT).returncode
    ok = code == 0 and target.exists()
    print(f"{stem} {kind}: exit {code} {'ok' if ok else 'MISSING'} {time.time()-start:.0f}s", flush=True)
    return ok

if __name__ == "__main__":
    if sys.argv[1] == "--all":
        stems, kinds = list(CHARACTERS), sys.argv[2:]
    else:
        stems, kinds = [sys.argv[1]], sys.argv[2:]
    failed = [(s, k) for k in kinds for s in stems if not run(s, k)]
    print("failed:", failed if failed else "none")
    sys.exit(1 if failed else 0)
