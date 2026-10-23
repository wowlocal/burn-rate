#!/usr/bin/env python3
"""Headless playtests: every founder in VS against the computer (with both
specials), and every mode on the mode list. Reports each run's events and
any engine boundary (a stop at an unsupported state).
Usage: playtest.py [BUILD_DIR] [RUN ...]   (RUN: vs-<stem>, demo, stage,
championship, 2on2, battle; default all)"""
import json, os, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith(("vs-", "demo", "stage", "champ", "2on2", "battle")) else \
    Path("/Volumes/NTSD-Builds/tasks/burnrate/build")
ONLY = [a for a in sys.argv[1:] if not a.startswith("/")]
STEMS = list(json.loads((ROOT / "art" / "characters.json").read_text()))
ATTACK, JUMP, DEFEND, UP, DOWN, LEFT, RIGHT = 65, 83, 68, 38, 40, 37, 39

def tap(c, vk): return f"{c} hold {vk} 1"

def vs(ordinal, cycles=1100):
    """Player 1 takes `ordinal`; one computer on Random moved to the next ordinal."""
    s = [tap(4, ATTACK), tap(10, ATTACK)]
    c = 14
    for _ in range(ordinal + 1): s.append(tap(c, RIGHT)); c += 2
    s += [tap(c + 2, ATTACK), tap(c + 6, ATTACK)]; ready = c + 6
    s.append(tap(ready + 160, ATTACK))                      # one computer player
    for k in range(3): s.append(tap(ready + 166 + 4 * k, RIGHT))
    s += [tap(ready + 178, ATTACK), tap(ready + 182, ATTACK), tap(ready + 188, UP), tap(ready + 192, UP), tap(ready + 196, ATTACK)]
    fight = ready + 280
    for k in range(6):                                       # D>A and D^A, then punches
        t = fight + 120 * k
        s += [tap(t, DEFEND), tap(t + 2, RIGHT if k % 2 == 0 else UP), tap(t + 4, ATTACK)]
        s += [tap(t + 40 + 8 * j, ATTACK) for j in range(5)]
    return "; ".join(s), cycles

def mode(row, cycles=1600):
    """Mode list row `row` by the arrow keys (with --original-menu-input: the
    keys reach the game, not the menu-gamepad cursor), then player 1 joins,
    picks the first founder, gets ready, and keeps confirming."""
    s, c = [], 6
    for _ in range(row): s.append(tap(c, DOWN)); c += 4
    t0 = c + 2; s.append(tap(t0, ATTACK))
    s += [tap(t0 + 10, ATTACK), tap(t0 + 14, RIGHT), tap(t0 + 18, ATTACK), tap(t0 + 22, ATTACK)]
    ready = t0 + 22
    s += [tap(ready + 160, ATTACK), tap(ready + 170, UP), tap(ready + 174, UP), tap(ready + 178, ATTACK)]
    s += [tap(c2, ATTACK) for c2 in range(ready + 220, cycles, 30)]
    return "; ".join(s), cycles

RUNS = {f"vs-{stem}": (lambda o=i: vs(o)) for i, stem in enumerate(STEMS)}
RUNS.update({"stage": lambda: mode(1), "championship": lambda: mode(2), "2on2": lambda: mode(3),
             "battle": lambda: mode(4), "demo": lambda: mode(5, 1400)})

def run(name):
    script, cycles = RUNS[name]()
    out = B / "runs" / "playtest" / name; out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*"):
        if f.is_file(): f.unlink()
    (out / "overlay").mkdir(exist_ok=True)
    extra = ["--original-menu-input"] if not name.startswith("vs-") else []
    args = [str(B / "swiftpm/release/BurnRateHeadless"), *extra, "--resources", str(B / "content"), "--music-dir", str(B / "content/OriginalMusic"),
            "--virtual-clock", "123456789", "8", "--no-network", "--mute-music", "--mute-sounds", "--overlay", str(out / "overlay"),
            "--script", "8 click 398 229; 90000 exit", "--loaded-script", f"{script}; {cycles} capture {out}/end.png; {cycles + 2} exit"]
    p = subprocess.run(args, capture_output=True, text=True, timeout=900)
    (out / "run.log").write_text(p.stdout + p.stderr)
    events, boundary, bodies = Counter(), None, 0
    for line in p.stdout.splitlines():
        try: e = json.loads(line)
        except ValueError: continue
        events[e.get("event")] += 1; bodies = max(bodies, e.get("gameplayBodies", 0) or 0)
        if e.get("event") == "boundary": boundary = e.get("error", "")[:300]
    ok = p.returncode == 0 and boundary is None
    print(f"{name:16} {'ok ' if ok else 'BAD'} exit {p.returncode} bodies {bodies:5} "
          f"launched {events['matchLaunched']} ended {events['menu']}" + (f"\n    boundary: {boundary}" if boundary else ""), flush=True)
    return ok

if __name__ == "__main__":
    names = ONLY or list(RUNS)
    bad = [n for n in names if not run(n)]
    print("bad:", bad or "none"); sys.exit(1 if bad else 0)
