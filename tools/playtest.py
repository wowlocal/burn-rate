#!/usr/bin/env python3
"""Headless playtests: every founder in VS against the computer (with both
specials), and every mode on the mode list. Reports each run's events and
any engine boundary (a stop at an unsupported state).
Usage: playtest.py [BUILD_DIR] [RUN ...]   (BUILD_DIR default build/; RUN:
vs-<stem>, demo, stage, act1..act6, championship, 2on2, battle; default all;
campaign, only by name, for a 1-HP check build)"""
import json, os, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith(("vs-", "demo", "stage", "act", "champ", "2on2", "battle", "campaign")) else \
    ROOT / "build"
ONLY = [a for a in sys.argv[1:] if a.split("-")[0] in ("vs", "demo", "stage", "championship", "2on2", "battle", "campaign") or a[:3] == "act"]
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

def select_mode(row):
    s, c = [], 6
    for _ in range(row): s.append(tap(c, DOWN)); c += 4
    return s, c + 2

def stage(cycles=3600):
    """Stage Mode: player 1 picks the first founder; the settings screen's
    cursor starts on its third option (Up, Up, then Attack starts)."""
    s, t0 = select_mode(1); s.append(tap(t0, ATTACK))
    s += [tap(t0 + 10, ATTACK), tap(t0 + 14, RIGHT), tap(t0 + 18, ATTACK), tap(t0 + 22, ATTACK)]
    ready = t0 + 22
    s += [tap(ready + 160, ATTACK), tap(ready + 170, UP), tap(ready + 174, UP), tap(ready + 178, ATTACK)]
    for c in range(ready + 260, cycles, 12):          # walk right and punch
        s += [f"{c} hold {RIGHT} 8", tap(c + 9, ATTACK)]
    return "; ".join(s), cycles

def act(n, cycles=3000, allies=0, difficulty=0):
    """Stage Mode from act `n` (docs/STORY.md): `allies` computer founders
    (Random) join player 1; on the settings screen Down reaches the STAGE row,
    Attack there steps the set by one, the DIFFICULTY row below takes
    `difficulty` Attacks, then Up reaches FIGHT! and Attack starts."""
    s, t0 = select_mode(1); s.append(tap(t0, ATTACK))
    s += [tap(t0 + 10, ATTACK), tap(t0 + 14, RIGHT), tap(t0 + 18, ATTACK), tap(t0 + 22, ATTACK)]
    ready = t0 + 22; c = ready + 156
    for _ in range(allies): c += 4; s.append(tap(c, RIGHT))
    c += 4; s.append(tap(c, ATTACK))
    for _ in range(allies): s += [tap(c + 6, ATTACK), tap(c + 12, ATTACK)]; c += 12
    c += 14; s.append(tap(c, DOWN)); c += 4
    for _ in range(n - 1): c += 8; s.append(tap(c, ATTACK))
    if difficulty: c += 8; s.append(tap(c, DOWN))
    for _ in range(difficulty): c += 8; s.append(tap(c, ATTACK))
    for _ in range(4 if difficulty else 3): c += 8; s.append(tap(c, UP))
    c += 8; s.append(tap(c, ATTACK))
    for k in range(c + 90, cycles, 12):      # walk right and punch (held 2: the result board misses 1-cycle taps)
        s += [f"{k} hold {RIGHT} 8", f"{k + 9} hold {ATTACK} 2"]
    return "; ".join(s), cycles

def battle(cycles=2400):
    """Battle Mode: player 1 and one computer (Random), then War menu 200
    (Attack opens 202) and 202 (Up, Up, Attack starts)."""
    s, t0 = select_mode(4); s.append(tap(t0, ATTACK))
    s += [tap(t0 + 10, ATTACK), tap(t0 + 14, RIGHT), tap(t0 + 18, ATTACK), tap(t0 + 22, ATTACK)]
    ready = t0 + 22
    s.append(tap(ready + 160, ATTACK))
    for k in range(3): s.append(tap(ready + 166 + 4 * k, RIGHT))
    s += [tap(ready + 178, ATTACK), tap(ready + 182, ATTACK)]
    w = ready + 220
    s += [tap(w, ATTACK), tap(w + 20, UP), tap(w + 24, UP), tap(w + 28, ATTACK)]
    s += [tap(c, ATTACK) for c in range(w + 80, cycles, 15)]
    return "; ".join(s), cycles

def championship(row=2, cycles=4000):
    """Championship (row 2) or 2 on 2 (row 3): menu 21 sets the eight entries
    (Left/Right picks a founder, Attack locks it, Left/Right toggles Computer/
    Human, Attack confirms; the first entry is player 1's, Human), menu 22
    (Right, Attack: no shuffle), menu 25 (Up, Up, Attack: start), then the
    bracket: Jump skips the waits, Attack claims and confirms player 1's
    pairing (Left/Right moves the Yes/No cursor)."""
    s, t0 = select_mode(row); s.append(tap(t0, ATTACK)); c = t0 + 20
    for entry in range(8):
        s += [tap(c, RIGHT), tap(c + 6, ATTACK)]
        if entry == 0: s.append(tap(c + 12, RIGHT))
        s.append(tap(c + 18, ATTACK)); c += 26
    s += [tap(c + 10, RIGHT), tap(c + 16, ATTACK), tap(c + 40, UP), tap(c + 46, UP), tap(c + 52, ATTACK)]
    for k in range(c + 120, cycles, 24):
        s += [tap(k, JUMP), tap(k + 8, LEFT), tap(k + 14, ATTACK)]
    return "; ".join(s), cycles

RUNS = {f"vs-{stem}": (lambda o=i: vs(o)) for i, stem in enumerate(STEMS)}
RUNS.update({"stage": stage, "championship": lambda: championship(2), "2on2": lambda: championship(3),
             "battle": battle, "demo": lambda: mode(5, 1400)})
RUNS.update({f"act{n}": (lambda n=n: act(n)) for n in range(1, 7)})
# Named only: the whole campaign with seven computer allies, meant for a check
# build whose enemies have 1 HP (BURNRATE_CHECK_STAGE_HP=1, docs/STORY.md).
CHECK_RUNS = {"campaign": lambda: act(1, 40000, allies=7)}
CAPTURES = [int(c) for c in os.environ.get("PLAYTEST_CAPTURES", "").split(",") if c]

def run(name):
    script, cycles = {**RUNS, **CHECK_RUNS}[name]()
    out = B / "runs" / "playtest" / name; out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*"):
        if f.is_file(): f.unlink()
    (out / "overlay").mkdir(exist_ok=True)
    extra = ["--original-menu-input"] if not name.startswith("vs-") else []
    args = [str(B / "swiftpm/release/BurnRateHeadless"), *extra, "--resources", str(B / "content"), "--music-dir", str(B / "content/OriginalMusic"),
            "--virtual-clock", "123456789", "8", "--no-network", "--mute-music", "--mute-sounds", "--overlay", str(out / "overlay"),
            "--script", "8 click 398 229; 90000 exit",
            "--loaded-script", f"{script}; " + "".join(f"{c} capture {out}/c{c}.png; " for c in CAPTURES) + f"{cycles} capture {out}/end.png; {cycles + 2} exit"]
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
