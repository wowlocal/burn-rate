#!/usr/bin/env python3
"""Generate Burn Rate's non-character art with Codex CLI's image generation:
stage backgrounds, projectiles/effects and title art. Raw outputs go to
$BURNRATE_RAW/misc (outside the repository), one PNG per job.

Usage: generate_misc.py JOB [JOB...]   (generate_misc.py --list)
"""
import os, subprocess, sys, time
from pathlib import Path

RAW = Path(os.environ.get("BURNRATE_RAW", "/Volumes/NTSD-Builds/tasks/burnrate/art/raw")) / "misc"
STYLE = ("in the style of 1990s arcade beat-'em-up pixel art: crisp pixels, limited palette, dark navy outlines, "
         "no text, no letters, no logos, no watermark")
STAGE = ("a side-view 2D fighting game stage background, wide landscape, {style}. The lower 45% of the image is a "
         "flat walkable floor seen from slightly above (a broad ground plane where fighters stand), the upper part "
         "shows the scenery. No people, no characters. Scene: {scene}")
JOBS = {
    "stage_demoday": STAGE.format(style=STYLE, scene="a startup Demo Day auditorium stage: a huge glowing screen with "
        "abstract charts, purple and orange spotlights, rows of empty investor seats in the dark background, a polished wooden stage floor."),
    "stage_sandhill": STAGE.format(style=STYLE, scene="Sand Hill Road at sunset: low modern venture-capital office buildings with "
        "glass fronts, palm trees, rolling golden hills, a pink and orange sky, a wide asphalt parking lot as the floor."),
    "stage_serverfarm": STAGE.format(style=STYLE, scene="a vast AI data center: long rows of server racks with blinking green and "
        "blue lights, cable trays overhead, cool blue lighting, a perforated grey raised-floor of tiles as the floor."),
    "stage_office": STAGE.format(style=STYLE, scene="an open-plan startup office: standing desks, giant monitors, bean bags, a "
        "ping-pong table, a kombucha tap, big windows with a city skyline, a light concrete floor."),
    "props": ("Use one flat solid magenta (#FF00FF) background everywhere, no gradients, no shadows, no floor. A sprite sheet of "
        f"small game effect and projectile sprites {STYLE}, arranged in a 6 columns x 4 rows grid with generous magenta space "
        "between them, each sprite centred in its cell, all at a similar small scale. Row 1: a fanned stack of flying presentation "
        "slides (3 animation frames, then 3 frames of a glowing cyan energy ball). Row 2: a rolled paper contract spinning (3 frames), "
        "a big gold coin spinning (3 frames). Row 3: a glowing green hexagon shield (3 frames), a glowing green GPU card spinning "
        "(3 frames). Row 4: a pink glowing chat bubble (2 frames), a crushed energy drink can (2 frames), a white golf ball with a "
        "motion streak (2 frames)."),
    "sparks": ("Use one flat solid magenta (#FF00FF) background everywhere, no gradients. A sprite sheet of fighting game hit "
        f"effects {STYLE}, 4 columns x 2 rows grid with generous magenta space: row 1 a white and yellow impact star burst growing "
        "over 4 frames; row 2 a blue guard-block spark over 4 frames."),
    "title": (f"A title screen background illustration for a 2D fighting game {STYLE}: a dramatic Silicon Valley skyline at "
        "night with glowing data-center lights, a giant burning dollar-bill shaped flame in the sky, neon purple and orange "
        "colours, lots of empty dark space in the middle and bottom for menu buttons. Landscape."),
}

def run(job):
    RAW.mkdir(parents=True, exist_ok=True)
    target = RAW / f"{job}.png"
    if target.exists():
        print(f"{target} exists, skipped", flush=True); return True
    text = (f"Use your image generation tool to create ONE image and save it in the current directory as {job}.png "
            f"(keep the tool's full resolution). {JOBS[job]} Then print the saved file's absolute path and pixel size.")
    (RAW / f"{job}.prompt.txt").write_text(text + "\n")
    start = time.time()
    with open(RAW / f"{job}.log", "w") as log:
        code = subprocess.run(["codex", "exec", "--skip-git-repo-check", "-C", str(RAW), "--sandbox", "workspace-write"],
                              input=text, text=True, stdout=log, stderr=subprocess.STDOUT).returncode
    ok = code == 0 and target.exists()
    print(f"{job}: exit {code} {'ok' if ok else 'MISSING'} {time.time()-start:.0f}s", flush=True)
    return ok

if __name__ == "__main__":
    if sys.argv[1:] == ["--list"]: print("\n".join(JOBS)); sys.exit(0)
    jobs = list(JOBS) if sys.argv[1:] == ["--all"] else sys.argv[1:]
    failed = [j for j in jobs if not run(j)]
    print("failed:", failed or "none"); sys.exit(1 if failed else 0)
