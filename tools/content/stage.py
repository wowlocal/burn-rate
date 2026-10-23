#!/usr/bin/env python3
"""Stage Burn Rate's content for BurnRateContentBuilder.

Writes STAGE_DIR/stage.json and every file it names: the DAT texts (plaintext;
the builder encrypts them), sprite sheets made by tools/art/process.py from
the raw Codex art, interface pictures, sounds, music and the initial record.
Pictures still to be drawn are plain placeholders.

Usage: stage.py STAGE_DIR   (raw art from $BURNRATE_RAW, default art/raw)
"""
import json, math, os, shutil, struct, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "art")); sys.path.insert(0, str(ROOT / "tools" / "content"))
import process  # noqa: E402

# The raw art: the repository's half-size archive (tools/art/archive.py) unless
# BURNRATE_RAW names the full-size Codex outputs.
RAW = Path(os.environ.get("BURNRATE_RAW", ROOT / "art" / "raw"))
CHARACTERS = json.loads((ROOT / "art" / "characters.json").read_text())

# --- names shared with Sources/BurnRateRules/BurnRateRules.swift ---------------
def two(n): return f"{n:02d}"
import interface  # noqa: E402  (tools/content)
import audio  # noqa: E402
FRONT, IFACE, MENU, WAR = interface.FRONT, interface.IFACE, interface.MENU, interface.WAR
COMMON = [f"data\\br_common_{two(i)}.wav" for i in range(18)]
MENU_SOUNDS = [f"data\\br_menu_{i}.wav" for i in range(5)]
MUSIC = [f"bgm\\{n}.wma" for n in ("main", "stage1", "stage2", "stage3", "stage4", "stage5", "boss1", "boss2")]
SCREEN = (794, 550)

# --- the initial record (0x44d000, 0xc3a8 bytes): zero but for these words ----
RECORD_BASE, RECORD_SIZE = 0x44d000, 0xc3a8
RECORD_WORDS = {
    0x44d78c: SCREEN[0], 0x44d790: SCREEN[1],  # client size (window, back buffer)
    0x44d068: 1,          # front menu bitmaps load while nonzero
    0x44d05c: 1,          # the first loading runs only for exactly 1
    0x44d020: 10,         # the mode screen after the first loading
    0x44d07c: 1,          # loaded menu bitmaps load while nonzero
    0x44dce8: 0x44a2b4,   # the replay writer's version pointer (exact)
    0x44d03c: 0x100,      # the game's version word
    # Battle Mode (War): eleven unit cells (founders 1-9, the coffee twice: cells
    # 9-10 are drawn as item icons), the preset display words, both sides'
    # defence (100 = x1.0), the setup's x offset and the War bitmaps' load flag.
    0x44d37c: 11, 0x44d380: 1, 0x44d384: 1, 0x44d758: 100, 0x44d75c: 100, 0x44d764: 44, 0x44d774: 1,
}
WAR_CELLS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100, 100]
# Presets 0-4 (shown as funding rounds), per cell: full-strength totals and
# on-screen counts (a cell meant to be empty needs both at 0).
WAR_PRESETS = [([6] * 9 + [3, 3], [3] * 11),                                   # balanced
               ([3] * 11, [3] * 11),                                           # inferior
               ([0, 9, 0, 0, 0, 0, 9, 0, 9, 3, 3], [0, 3, 0, 0, 0, 0, 3, 0, 3, 3, 3]),   # ranged: Vector, Prompt, Angel
               ([9, 0, 0, 9, 0, 9, 0, 0, 0, 3, 3], [3, 0, 0, 3, 0, 3, 0, 0, 0, 3, 3]),   # melee: Blitz, Moonshot, Gigawatt
               ([0, 0, 0, 0, 0, 9, 0, 0, 0, 3, 3], [0, 0, 0, 0, 0, 3, 0, 0, 0, 3, 3])]   # giant: Gigawatt
for _cell, _id in enumerate(WAR_CELLS): RECORD_WORDS[0x44d350 + 4 * _cell] = _id
for _p, (_totals, _active) in enumerate(WAR_PRESETS):
    for _cell in range(11):
        RECORD_WORDS[0x44d388 + 4 * (_p * 11 + _cell)] = _totals[_cell]
        RECORD_WORDS[0x44d468 + 4 * (_p * 11 + _cell)] = _active[_cell]

# --- file writers -----------------------------------------------------------
bmp_bytes = process.bmp_bytes

def dib_bytes(rgb):
    return bmp_bytes(rgb)[14:]

def wav_bytes(samples, rate=22050):
    data = bytes(int(max(0, min(255, 128 + s * 127))) for s in samples)
    fmt = struct.pack("<HHIIHH", 1, 1, rate, rate, 1, 8)
    body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(data)) + data
    if len(data) % 2: body += b"\0"
    return b"RIFF" + struct.pack("<I", len(body)) + body

def tone(seconds, freq0, freq1=None, noise=0.0, volume=0.6, rate=22050, seed=1):
    rng = np.random.default_rng(seed); n = int(seconds * rate); out = []
    freq1 = freq0 if freq1 is None else freq1; phase = 0.0
    for i in range(n):
        t = i / n; f = freq0 + (freq1 - freq0) * t; phase += 2 * math.pi * f / rate
        env = (1 - t) ** 2 * min(1.0, i / 80)
        out.append(volume * env * ((1 - noise) * math.sin(phase) + noise * (rng.random() * 2 - 1)))
    return out

def panel(w, h, fill, edge=(250, 250, 250), label=None):
    img = Image.new("RGB", (w, h), fill); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=edge)
    if label: d.text((4, 2), label, fill=edge)
    a = np.asarray(img).copy(); a[a.sum(axis=-1) == 0] = (8, 8, 16); return a

class Stage:
    def __init__(self, root):
        self.root = root
        if root.exists(): shutil.rmtree(root)
        root.mkdir(parents=True)
        self.doc = {"exeLabel": "Burn Rate content (no reference EXE)", "absentFiles": ["data/ad0.txt"],
                    "startup": [], "catalog": [], "commonSounds": [], "interfaceBitmaps": [], "menuBitmaps": [],
                    "warBitmaps": [], "arenas": [], "music": {"sampleRate": 22050, "entries": []}}
    def file(self, rel, data):
        p = self.root / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, (bytes, bytearray)) else data.encode("ascii")); return rel
    def catalog(self, name, kind, rel, data, encrypt=False):
        self.file(rel, data)
        e = {"name": name, "kind": kind, "source": rel}
        if encrypt: e["encrypt"] = True
        self.doc["catalog"].append(e)
    def write(self):
        (self.root / "stage.json").write_text(json.dumps(self.doc, indent=1))

# --- DAT text -----------------------------------------------------------------
CX, CY = process.CENTER_X, process.BASELINE
# Boxes and points are given relative to the feet (CX, CY) and converted to the
# cell's top-left coordinates the DAT uses.
def body(dx, dy, w, h): return f"bdy:\nkind: 0 x: {CX + dx} y: {CY + dy} w: {w} h: {h}\nbdy_end:\n"
BODY = body(-14, -63, 28, 63)
LOW_BODY = body(-17, -41, 34, 41)
SWING = "data\\br_swing.wav"   # frame sound paths stay under 20 characters

def itr(dx, dy, w, h, dvx, fall, injury, arest=8, bdefend=16, dvy=0):
    return (f"itr:\nkind: 0 x: {CX + dx} y: {CY + dy} w: {w} h: {h} dvx: {dvx} dvy: {dvy} fall: {fall} arest: {arest} "
            f"bdefend: {bdefend} injury: {injury}\nitr_end:\n")

def frame(n, name, pic, state, wait, nxt, body=BODY, extra="", dvx=0, dvy=0):
    return (f"<frame> {n} {name}\npic: {pic} state: {state} wait: {wait} next: {nxt} dvx: {dvx} dvy: {dvy} dvz: 0 "
            f"centerx: {CX} centery: {CY}\n{extra}{body}<frame_end>\n\n")

# Pictures (tools/art/process.py order): sheet A 0-11, sheet B 12-23, sheet C 24-31.
P = dict(idle1=0, idle2=1, walk=[2, 3, 4, 5], run=[6, 7, 8], wind=9, punch=10, kick=11,
         crouch=12, tuck=13, top=14, airkick=15, lunge=16, block=17, hitA=18, hitB=19, flung=20, lying=21,
         rise=22, land=23, sp_wind=24, sp_release=25, uppercut=26, charge=27, backfist=28, victory=29, tired=30, taunt=31)

def character_text(c, stem):
    s = c.get("stats", {})
    walk, run = s.get("walk", 4.0), s.get("run", 8.0)
    power = s.get("power", 1.0)
    t = (f"\n<bmp_begin>\nname: {c['name'].replace(' ', '_')}\nhead: sprite\\br\\{stem}_f.bmp\nsmall: sprite\\br\\{stem}_s.bmp\n"
         f"file(0-39): sprite\\br\\{stem}_0.bmp  w: {process.CELL}  h: {process.CELL}  row: {process.COLUMNS}  col: {process.ROWS}\n"
         f"walking_frame_rate 3\nwalking_speed {walk}\nwalking_speedz {walk / 2}\nrunning_frame_rate 3\n"
         f"running_speed {run}\nrunning_speedz {run / 6}\nheavy_walking_speed 3.0\nheavy_walking_speedz 1.5\n"
         f"heavy_running_speed 5.0\nheavy_running_speedz 0.75\njump_height {s.get('jump', -15.5)}\njump_distance 8.5\n"
         f"jump_distancez 3.5\ndash_height -9.5\ndash_distance 15.0\ndash_distancez 3.5\n"
         f"rowing_height -2.0\nrowing_distance 4.0\n<bmp_end>\n\n")
    def dmg(v): return int(round(v * power))
    combos = "hit_Fa: 240 hit_Ua: 250\n"
    t += frame(0, "standing", P["idle1"], 0, 8, 1, extra=combos) + frame(1, "standing", P["idle2"], 0, 8, 2, extra=combos)
    t += frame(2, "standing", P["idle1"], 0, 8, 3, extra=combos) + frame(3, "standing", P["idle2"], 0, 8, 999, extra=combos)
    for i in range(4): t += frame(5 + i, "walking", P["walk"][i], 1, 3, 999, extra=combos)
    for i in range(3): t += frame(9 + i, "running", P["run"][i], 2, 2, 999)
    # Standing attacks: 60 (jab) or 65 (kick), drawn at random by the engine.
    t += frame(60, "punch", P["wind"], 3, 1, 61)
    t += frame(61, "punch", P["punch"], 3, 2, 62, extra=f"sound: {SWING}\n" + itr(6, -51, 40, 16, 4, 20, dmg(28)))
    t += frame(62, "punch", P["wind"], 3, 1, 999)
    t += frame(65, "kick", P["idle1"], 3, 1, 66)
    t += frame(66, "kick", P["kick"], 3, 3, 67, extra=f"sound: {SWING}\n" + itr(3, -69, 42, 24, 6, 35, dmg(34), arest=10))
    t += frame(67, "kick", P["idle1"], 3, 2, 999)
    # Jump attack, run attack, dash attack.
    t += frame(80, "jump_attack", P["airkick"], 3, 2, 81, extra=f"sound: {SWING}\n" + itr(1, -47, 40, 30, 8, 70, dmg(40)))
    t += frame(81, "jump_attack", P["airkick"], 3, 6, 999)
    t += frame(85, "run_attack", P["charge"], 3, 3, 86, dvx=4, extra=f"sound: {SWING}\n" + itr(1, -61, 36, 50, 12, 70, dmg(45), arest=14))
    t += frame(86, "run_attack", P["charge"], 3, 4, 999)
    t += frame(90, "dash_attack", P["airkick"], 3, 2, 91, extra=f"sound: {SWING}\n" + itr(1, -47, 40, 30, 10, 70, dmg(45)))
    t += frame(91, "dash_attack", P["airkick"], 3, 6, 999)
    # Rowing (a recovery flip from a fall, or defend while running).
    for n in (100, 108): t += frame(n, "rowing", P["tuck"], 6, 3, n + 1, body="") + frame(n + 1, "rowing", P["tuck"], 6, 3, 999, body="")
    t += frame(102, "rolling", P["tuck"], 6, 3, 103, dvx=8, body=LOW_BODY) + frame(103, "rolling", P["crouch"], 6, 3, 999, body=LOW_BODY)
    # Defence.
    t += frame(110, "defend", P["block"], 7, 12, 999)
    t += frame(111, "defend", P["block"], 7, 4, 110)
    t += frame(112, "broken_defend", P["hitB"], 8, 8, 999)
    # Falling (the physics chooses among them by vertical speed), lying, rising.
    for n in range(180, 192): t += frame(n, "falling", P["flung"], 12, 2, 0)
    t += frame(230, "lying", P["lying"], 14, 22, 232, body="") + frame(231, "lying", P["lying"], 14, 22, 232, body="")
    t += frame(232, "getting_up", P["rise"], 14, 5, 999, body="")
    # Injuries.
    t += frame(220, "injured", P["hitA"], 11, 5, 999)
    for n in (222, 224): t += frame(n, "injured", P["hitA"], 11, 2, n + 1) + frame(n + 1, "injured", P["hitB"], 11, 3, 999)
    t += frame(226, "dazed", P["hitB"], 16, 3, 227) + frame(227, "dazed", P["tired"], 16, 6, 999)
    # Jump, dash, landings.
    t += frame(210, "jump", P["crouch"], 4, 1, 211, body=LOW_BODY) + frame(211, "jump", P["tuck"], 4, 1, 212)
    t += frame(212, "jump", P["top"], 4, 1, 0)
    t += frame(213, "dash", P["lunge"], 5, 1, 0) + frame(214, "dash", P["top"], 5, 1, 0)
    t += frame(216, "dash", P["lunge"], 5, 1, 0) + frame(217, "dash", P["top"], 5, 1, 0)
    t += frame(215, "crouch", P["land"], 15, 2, 999, body=LOW_BODY) + frame(219, "crouch", P["land"], 15, 2, 999, body=LOW_BODY)
    t += frame(218, "stop_running", P["land"], 15, 3, 999, body=LOW_BODY)
    # Specials: defend, forward, attack throws the signature projectile; defend,
    # up, attack is a launching uppercut.
    pid = PROJECTILE_BASE + c["id"] - 1
    t += frame(240, "signature", P["sp_wind"], 3, 3, 241, extra="mp: 150\n")
    t += frame(241, "signature", P["sp_release"], 3, 4, 242, extra=f"sound: {SWING}\nopoint:\nkind: 1 x: {CX + 23} y: {CY - 41} action: 100 dvx: 0 dvy: 0 oid: {pid} facing: 0\nopoint_end:\n")
    t += frame(242, "signature", P["sp_release"], 3, 5, 999)
    t += frame(250, "uppercut", P["wind"], 3, 1, 251, extra="mp: 60\n")
    t += frame(251, "uppercut", P["uppercut"], 3, 4, 252, extra=f"sound: {SWING}\n" + itr(-3, -77, 40, 52, 3, 70, dmg(48), arest=14, dvy=-12))
    t += frame(252, "uppercut", P["uppercut"], 3, 4, 999)
    return t

# Projectiles: IDs 200.. (one per fighter, by fighter ID), pictures from the
# props sheet (6 x 4, reading order): slides 0-2, energy ball 3-5, contract
# 6-8, coin 9-11, shield 12-14, GPU 15-17, chat bubble 18-19, can 20-21,
# golf ball 22-23.
PROJECTILE_BASE, PROJECTILE_CELL = 200, 39
PROJECTILE_PICS = {"blitz": [0, 1, 2], "vector": [3, 4, 5], "vesta": [6, 7, 8], "moonshot": [9, 10, 11], "ada": [12, 13, 14],
                   "gigawatt": [15, 16, 17], "prompt": [18, 19], "intern": [20, 21], "angel": [22, 23],
                   "viral": [24, 25, 26]}   # 24-26: props2.png (sound-wave rings)
def projectile_text(name, stem, pictures):
    cell = PROJECTILE_CELL
    t = (f"\n<bmp_begin>\nname: {name}\nfile(0-3): sprite\\br\\{stem}_p.bmp  w: {cell}  h: {cell}  row: 4  col: 1\n<bmp_end>\n\n")
    def f(n, name, pic, state, wait, nxt, extra="", dvx=0):
        return (f"<frame> {n} {name}\npic: {pic} state: {state} wait: {wait} next: {nxt} dvx: {dvx} dvy: 0 dvz: 0 "
                f"centerx: {cell // 2} centery: {cell // 2}\n{extra}<frame_end>\n\n")
    flying = ("bdy:\nkind: 0 x: 6 y: 6 w: 27 h: 27\nbdy_end:\n"
              "itr:\nkind: 0 x: 4 y: 6 w: 31 h: 27 dvx: 9 fall: 70 arest: 20 bdefend: 40 injury: 55 zwidth: 12\nitr_end:\n")
    # Frames 100-139 fly (state 3000) and then vanish (next 1000); a hit sends
    # the engine to 10 (it hit), 20 (hit by a projectile) or 30 (hit by a fighter).
    for i in range(40):
        t += f(100 + i, "flying", pictures[i % len(pictures)], 3000, 1, 101 + i if i < 39 else 1000, flying, dvx=12)
    for base, state in ((10, 3001), (20, 3002), (30, 3003)):
        t += f(base, "hit", pictures[-1], state, 1, base + 1) + f(base + 1, "hit", pictures[0], state, 1, 1000)
    return t

ITEM_CELL = 31
def item_text(name, stem):
    t = (f"\n<bmp_begin>\nname: {name}\nfile(0-3): sprite\\br\\{stem}_0.bmp  w: {ITEM_CELL}  h: {ITEM_CELL}  row: 4  col: 1\n"
         f"weapon_hp: 60\nweapon_drop_hurt: 7\n<bmp_end>\n\n")
    def f(n, name, pic, state, nxt):
        return (f"<frame> {n} {name}\npic: {pic} state: {state} wait: 1 next: {nxt} dvx: 0 dvy: 0 dvz: 0 "
                f"centerx: {ITEM_CELL // 2} centery: {ITEM_CELL - 1}\n<frame_end>\n\n")
    for i in range(4): t += f(i, "in_the_sky", i, 1000, 0 if i == 3 else i + 1)
    return t + f(60, "on_ground", 0, 1004, 0) + f(70, "on_ground", 0, 1004, 0)

# Stages: (catalog id, name, folder, raw image). The backdrop is the whole
# picture scaled to the screen's height and scrolled with parallax (a layer
# narrower than the stage moves less, OriginalBackgroundDrawing); the floor is a
# seamless band from the picture's lower part, as wide as the stage.
STAGES = [(0, "Demo_Day", "demoday", "stage_demoday"), (1, "Sand_Hill_Road", "sandhill", "stage_sandhill"),
          (2, "Server_Farm", "serverfarm", "stage_serverfarm"), (3, "Open_Office", "office", "stage_office"),
          (4, "Garage", "garage", "stage_garage"), (5, "Board_Room", "boardroom", "stage_boardroom")]
STAGE_WIDTH, FLOOR_TOP, Z_RANGE = 1600, 300, (322, 512)
def bg_paths(folder):
    base = f"bg\\br\\{folder}\\"
    return base + "bg.dat", base + "s.bmp", base + "back.bmp", base + "floor.bmp"
def background_text(name, folder, back_width):
    dat, shadow, back, floor = bg_paths(folder)
    return (f"\nname: {name}\nwidth: {STAGE_WIDTH}\nzboundary: {Z_RANGE[0]} {Z_RANGE[1]}\nshadow: {shadow} shadowsize: 18 5\n"
            f"layer: {back}\ntransparency: 0 width: {back_width} x: 0 y: 0 height: {SCREEN[1]} loop: 0\nlayer_end\n"
            f"layer: {floor}\ntransparency: 0 width: {STAGE_WIDTH} x: 0 y: {FLOOR_TOP} height: {SCREEN[1] - FLOOR_TOP} loop: 0\nlayer_end\n\n")

def stage_pictures(raw_image):
    """The backdrop (screen height) and the floor band (STAGE_WIDTH wide)."""
    if raw_image.exists():
        img = Image.open(raw_image).convert("RGB")
        w = round(img.width * SCREEN[1] / img.height)
        back = np.asarray(img.resize((max(w, SCREEN[0]), SCREEN[1]), Image.LANCZOS)).copy()
    else:
        back = np.zeros((SCREEN[1], SCREEN[0], 3), np.uint8)
        back[:] = np.linspace([40, 30, 90], [230, 120, 90], SCREEN[1])[:, None, :].astype(np.uint8)
    band = back[FLOOR_TOP:, :]
    cw = min(band.shape[1], 400); x0 = (band.shape[1] - cw) // 2
    tile = band[:, x0:x0 + cw]; pair = np.concatenate([tile, tile[:, ::-1]], axis=1)
    floor = np.tile(pair, (1, STAGE_WIDTH // pair.shape[1] + 1, 1))[:, :STAGE_WIDTH].copy()
    for a in (back, floor): a[a.sum(axis=-1) == 0] = (8, 8, 16)
    return back, floor

# Stage Mode: the campaign of docs/STORY.md, six acts as the engine's six
# sets (stage ids 10*act + 0..3; a set ends at its first undefined id, the
# last set brings the ENDING). Missions x-1..x-3 have two phases (the camera
# stops at bound 800, then 1500); x-4 is the act's boss, whose soldiers keep
# coming until the boss falls. No `music:`: the engine rejects phase music.
# Entries: (founder, hp, times) or (founder, hp, "boss" | "soldier").
FOUNDER = {"blitz": 1, "vector": 2, "vesta": 3, "moonshot": 4, "ada": 5, "gigawatt": 6, "prompt": 7, "intern": 8,
           "angel": 9, "viral": 10}
ACTS = [
    [   # Act 1, Pre-Seed (the Garage)
        [[("intern", 120, 3)], [("intern", 120, 2), ("prompt", 150, 1)]],
        [[("viral", 180, 1), ("intern", 120, 2)], [("viral", 220, 1), ("prompt", 180, 1)]],
        [[("angel", 200, 1), ("intern", 120, 2)], [("angel", 250, 1), ("moonshot", 200, 1)]],
        [[("blitz", 600, "boss"), ("intern", 120, "soldier"), ("intern", 120, "soldier")]],
    ],
    [   # Act 2, Seed (Demo Day)
        [[("prompt", 200, 1), ("viral", 200, 1)], [("intern", 130, 3), ("prompt", 220, 1)]],
        [[("vector", 220, 1), ("intern", 130, 2)], [("vector", 260, 1), ("ada", 220, 1)]],
        [[("moonshot", 240, 1), ("viral", 220, 1)], [("moonshot", 260, 1), ("blitz", 240, 1)]],
        [[("moonshot", 700, "boss"), ("viral", 180, "soldier"), ("viral", 180, "soldier")]],
    ],
    [   # Act 3, Series A (Sand Hill Road)
        [[("angel", 220, 1), ("intern", 130, 2)], [("angel", 250, 2)]],
        [[("vesta", 250, 1), ("angel", 220, 1)], [("vesta", 280, 1), ("moonshot", 250, 1)]],
        [[("vesta", 280, 2)], [("vesta", 280, 1), ("angel", 250, 1), ("intern", 130, 1)]],
        [[("vesta", 800, "boss"), ("angel", 200, "soldier"), ("angel", 200, "soldier")]],
    ],
    [   # Act 4, Hypergrowth (the Open Office)
        [[("intern", 130, 4)], [("intern", 130, 2), ("prompt", 220, 1)]],
        [[("viral", 260, 1), ("moonshot", 260, 1)], [("blitz", 260, 1), ("viral", 260, 1)]],
        [[("vector", 280, 1)], [("vector", 280, 1), ("ada", 260, 1)]],
        [[("ada", 850, "boss"), ("vector", 220, "soldier"), ("vector", 220, "soldier")]],
    ],
    [   # Act 5, the Compute War (the Server Farm)
        [[("intern", 140, 3)], [("intern", 140, 2), ("vector", 280, 1)]],
        [[("vector", 300, 2)], [("vector", 300, 1), ("ada", 280, 1)]],
        [[("gigawatt", 400, 1)], [("gigawatt", 400, 1), ("blitz", 280, 1)]],
        [[("gigawatt", 1000, "boss"), ("intern", 140, "soldier"), ("vector", 240, "soldier")]],
    ],
    [   # Act 6, the Last Round (the Board Room)
        [[("angel", 300, 1), ("vesta", 300, 1)], [("moonshot", 300, 1), ("angel", 300, 1)]],
        [[("blitz", 320, 1), ("viral", 300, 1)], [("prompt", 300, 1), ("blitz", 320, 1)]],
        [[("ada", 320, 1), ("vector", 320, 1)], [("gigawatt", 450, 1), ("vector", 320, 1)]],
        [[("vesta", 900, "boss"), ("gigawatt", 1100, "boss"), ("angel", 220, "soldier"), ("angel", 220, "soldier")]],
    ],
]
PHASE_BOUNDS = (800, 1500)

def stage_text():
    """stage.dat. BURNRATE_CHECK_STAGE_HP (a check build only, never shipped)
    gives every enemy that HP, so a scripted run can walk all six acts."""
    check_hp = os.environ.get("BURNRATE_CHECK_STAGE_HP")
    out = "\n"
    for act, missions in enumerate(ACTS):
        for m, phases in enumerate(missions):
            out += f"<stage> id: {10 * act + m}\n"
            bounds = PHASE_BOUNDS if len(phases) == 2 else PHASE_BOUNDS[1:]
            for bound, entries in zip(bounds, phases):
                out += f"<phase> bound: {bound}\n"
                for who, hp, extra in entries:
                    hp = int(check_hp) if check_hp else hp
                    tail = f" <{extra}>" if isinstance(extra, str) else (f" times: {extra}" if extra > 1 else "")
                    out += f"id: {FOUNDER[who]} hp: {hp}{tail}\n"
                out += "<phase_end>\n"
            out += "<stage_end>\n\n"
    return out

def control_text():
    keys = [[0x26, 0x28, 0x25, 0x27, 0x41, 0x53, 0x44],          # P1: arrows, A attack, S jump, D defend
            [0x54, 0x47, 0x46, 0x48, 0x5a, 0x58, 0x43],          # P2: T G F H, Z X C
            [0x49, 0x4b, 0x4a, 0x4c, 0x55, 0x4f, 0x50],          # P3: I K J L, U O P
            [0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37]]          # P4: digits
    lines = [" ".join(str(v) for v in [0] + k + [5, 6, 7]) for k in keys]
    lines += ["Founder CoFounder Angel Seed", "0", "1", "Burn Rate settings", "made by tools/content/stage.py", "end of settings"]
    return "\r\n".join(lines)

def main():
    root = Path(sys.argv[1]); st = Stage(root)
    # Startup: record, MENU_BACK1..13, front bitmaps, data files, menu WAVs.
    rec = bytearray(RECORD_SIZE)
    for addr, value in RECORD_WORDS.items(): rec[addr - RECORD_BASE:addr - RECORD_BASE + 4] = struct.pack("<I", value)
    st.doc["startup"].append({"path": "initial.bin", "source": st.file("startup/initial.bin", bytes(rec))})
    ui = interface.build(RAW / "misc", ROOT / "Sources" / "BurnRateRules" / "GeneratedInterface.swift")
    for n in range(1, 14):
        st.doc["startup"].append({"path": f"bitmaps/MENU_BACK{n}.dib", "source": st.file(f"startup/MENU_BACK{n}.dib", dib_bytes(ui[f"MENU_BACK{n}"]))})
    for name in dict.fromkeys(FRONT):   # distinct names; the cursor is listed twice
        st.doc["startup"].append({"path": f"bitmaps/{name}.dib", "source": st.file(f"startup/{name}.dib", dib_bytes(ui[name]))})
    st.doc["startup"].append({"path": "data/control.txt", "source": st.file("startup/control.txt", control_text())})
    st.doc["startup"].append({"path": "data/adinfo.txt", "source": st.file("startup/adinfo.txt", "dont_update 0 5 <end>\r\n")})
    for i, (name, data) in enumerate(zip(MENU_SOUNDS, audio.menu_sounds())):
        st.doc["startup"].append({"path": name.replace("\\", "/"), "source": st.file(f"startup/menu_{i}.wav", data)})

    # Catalog.
    objects = ""
    sprite_out = root / "catalog" / "sprite"
    for stem, c in CHARACTERS.items():
        has_art = (RAW / stem / f"{stem}_A.png").exists()
        args = [str(RAW), stem, str(sprite_out), "--height", str(c.get("height", process.HEIGHT))]
        args += [] if has_art else ["--source-stem", "blitz", "--tint", str(37 * c["id"])]
        subprocess.run([sys.executable, str(ROOT / "tools" / "art" / "process.py")] + args, check=True)
        dat = f"data\\br_{stem}.dat"
        st.catalog(dat, "file", f"catalog/{stem}.txt", character_text(c, stem), encrypt=True)
        for suffix in ("_0.bmp", "_0_mirror.bmp", "_f.bmp", "_s.bmp"):
            st.doc["catalog"].append({"name": f"sprite\\br\\{stem}{suffix}", "kind": "bitmapFile", "source": f"catalog/sprite/{stem}{suffix}"})
        objects += f"id: {c['id']} type: 0 file: {dat}\r\n"
    # One item (the engine's random drop needs a candidate): a coffee cup.
    cup = np.zeros((ITEM_CELL, ITEM_CELL * 4 + 3, 3), np.uint8)
    cup_src = RAW / "items" / "cup.png"
    if cup_src.exists():
        img = Image.open(cup_src).convert("RGB"); a = np.asarray(img); fg = ~process.magenta(a)
        ys, xs = np.nonzero(fg); box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        rgb, keep = process.render(a, fg, box, (ITEM_CELL - 9) / max(box[2] - box[0], box[3] - box[1]))
        for i in range(4):
            h, w = keep.shape; ox = i * (ITEM_CELL + 1) + (ITEM_CELL - w) // 2; oy = ITEM_CELL - 1 - h
            region = cup[oy:oy + h, ox:ox + w]; region[keep] = rgb[keep]
    else:
        cup[8:30, 4:27] = (200, 180, 140)
    st.catalog("data\\br_coffee.dat", "file", "catalog/coffee.txt", item_text("Cold_Brew", "coffee"), encrypt=True)
    st.catalog("sprite\\br\\coffee_0.bmp", "bitmapFile", "catalog/sprite/coffee_0.bmp", bmp_bytes(cup))
    st.catalog("sprite\\br\\coffee_0_mirror.bmp", "bitmapFile", "catalog/sprite/coffee_0_mirror.bmp", bmp_bytes(cup[:, ::-1].copy()))
    objects += "id: 100 type: 1 file: data\\br_coffee.dat\r\n"
    props = RAW / "misc" / "props.png"
    if props.exists():
        sprites = []   # (image array, foreground, box) per projectile picture, props.png then props2.png
        for src, count in ((props, 24), (RAW / "misc" / "props2.png", 3)):
            if src.exists():
                a, fg, boxes = process.find_poses(Image.open(src), count, min_cells=20)
                sprites += [(a, fg, b) for b in boxes]
        for stem, c in CHARACTERS.items():
            pics = [i for i in PROJECTILE_PICS[stem] if i < len(sprites)] or PROJECTILE_PICS["blitz"]; cell = PROJECTILE_CELL
            sizes = [max(sprites[i][2][2] - sprites[i][2][0], sprites[i][2][3] - sprites[i][2][1]) for i in pics]
            scale = (cell - 7) / max(sizes)
            sheet = np.zeros((cell, 4 * (cell + 1), 3), np.uint8)
            for k, i in enumerate(pics):
                a, fg, box = sprites[i]
                rgb, keep = process.render(a, fg, box, scale)
                h, w = keep.shape; ox = k * (cell + 1) + (cell - w) // 2; oy = (cell - h) // 2
                region = sheet[oy:oy + h, ox:ox + w]; region[keep] = rgb[keep]
            dat = f"data\\br_{stem}_p.dat"; pid = PROJECTILE_BASE + c["id"] - 1
            st.catalog(dat, "file", f"catalog/{stem}_p.txt", projectile_text(f"{c['name'].replace(' ', '_')}_shot", stem, list(range(len(pics)))), encrypt=True)
            st.catalog(f"sprite\\br\\{stem}_p.bmp", "bitmapFile", f"catalog/sprite/{stem}_p.bmp", bmp_bytes(sheet))
            st.catalog(f"sprite\\br\\{stem}_p_mirror.bmp", "bitmapFile", f"catalog/sprite/{stem}_p_mirror.bmp", bmp_bytes(sheet[:, ::-1].copy()))
            objects += f"id: {pid} type: 3 file: {dat}\r\n"
    backgrounds = "".join(f"id: {i} file: {bg_paths(folder)[0]}\r\n" for i, _, folder, _ in STAGES)
    catalog_txt = f"<object>\r\n{objects}<object_end>\r\n\r\n<background>\r\n{backgrounds}<background_end>\r\n"
    st.catalog("data\\data.txt", "file", "catalog/data.txt", catalog_txt)
    st.catalog("data\\stage.dat", "file", "catalog/stage.txt", stage_text(), encrypt=True)
    st.catalog(SWING, "file", "catalog/swing.wav", audio.swing())
    shadow = np.zeros((10, 36, 3), np.uint8)
    yy, xx = np.mgrid[0:10, 0:36]; shadow[((xx - 17.5) / 18) ** 2 + ((yy - 4.5) / 5) ** 2 <= 1] = (24, 24, 30)
    for _, name, folder, raw in STAGES:
        back, floor = stage_pictures(RAW / "misc" / f"{raw}.png")
        dat, shadow_path, back_path, floor_path = bg_paths(folder)
        st.catalog(dat, "file", f"catalog/bg_{folder}.txt", background_text(name, folder, back.shape[1]), encrypt=True)
        for path, arr in ((shadow_path, shadow), (back_path, back), (floor_path, floor)):
            rel = "arena/" + path.replace("\\", "/")
            st.file(rel, bmp_bytes(arr)); st.doc["arenas"].append({"name": path, "source": rel})
        st.doc["catalog"].append({"name": shadow_path, "kind": "bitmapFile", "source": "arena/" + shadow_path.replace("\\", "/")})
    # Built-ins the registry requests before the catalog.
    road = interface.road(RAW / "misc")
    for i, name in enumerate(["shadow1", "back99_1", "back99_2", "back99_3"]):
        st.catalog(name, "dib", f"catalog/{name}.dib", dib_bytes(shadow if i == 0 else road[i - 1]))
    for name in MUSIC:
        st.catalog(name, "music", f"catalog/{name.split(chr(92))[1]}.txt", f"Burn Rate placeholder for {name}; never read\n")

    # Common sounds, interface, menus, War menu.
    for i, (name, data) in enumerate(zip(COMMON, audio.common_sounds())):
        st.doc["commonSounds"].append({"name": name, "source": st.file(f"common/{i}.wav", data)})
    for key, names in (("interfaceBitmaps", IFACE), ("menuBitmaps", MENU), ("warBitmaps", WAR)):
        for name in names:
            st.doc[key].append({"name": name, "source": st.file(f"{key}/{name}.dib", dib_bytes(ui[name]))})

    # Music: synthesized chiptune loops (AVAudioPlayer plays WAV on the Mac).
    st.doc["music"]["sampleRate"] = audio.RATE
    for name, (stem, data, frames) in zip(MUSIC, audio.music()):
        st.doc["music"]["entries"].append({"name": name, "resource": f"{stem}.wav", "frames": frames,
                                           "source": st.file(f"music/{stem}.wav", data)})
    st.write()
    print(f"staged {len(st.doc['catalog'])} catalog entries into {root}")

if __name__ == "__main__":
    main()
