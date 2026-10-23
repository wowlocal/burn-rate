#!/usr/bin/env python3
"""Burn Rate's interface art for the engine's fixed slots (docs/INTERFACE_SLOTS.md).

Everything is drawn here (PIL) or fitted from Codex art in $BURNRATE_RAW/misc
(logo, title, random face, device icons, sparks). Frame sizes and on-screen
positions are the engine's (its screens draw fixed frame indices at fixed
places); the atlases and their rectangles are ours. `build()` returns the
pictures by name and writes Sources/BurnRateRules/GeneratedInterface.swift
with the slot names and the front sheets' rectangles.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SUP = "/System/Library/Fonts/Supplemental/"
FONT_LABEL = SUP + "DIN Condensed Bold.ttf"
FONT_TITLE = SUP + "Arial Black.ttf"
FONT_MONO = "/System/Library/Fonts/Menlo.ttc"
SCREEN = (794, 550)

INK = (240, 236, 222)
PANEL, PANEL_EDGE = (24, 26, 56), (255, 132, 40)
HOT, HOT_INK = (255, 112, 28), (255, 255, 255)
DIM = (120, 122, 150)
NEAR_BLACK = (8, 8, 16)

# Names, one per engine slot (the engine fixes only the list lengths).
FRONT = (["BR_CURSOR"] + [f"BR_CLIP{i}" for i in range(1, 8)] + ["BR_WAIT", "BR_SLOGAN", "BR_ENDING", "BR_CURSOR"]
         + [f"BR_DEVICE{i}" for i in range(2, 7)] + ["BR_FRAME"] + [f"BR_WORDS{i}" for i in range(6)])
IFACE = ["BR_PAUSE", "BR_DEMO", "BR_BOARD1", "BR_BOARD2", "BR_BOARD3", "BR_BOARD4", "BR_WIN_ALIVE", "BR_WIN_DEAD",
         "BR_LOSE_DEAD", "BR_BARS"]
MENU = ["BR_CHARMENU"] + [f"BR_CM{i}" for i in range(1, 6)] + ["BR_CMA", "BR_CMA2", "BR_CMC", "BR_RFACE", "BR_SPARK"]
WAR = ["BR_BATTLEMODE", "BR_BATTLETROOPS"]
WAR_MODE_FRAMES = [[0, 0, 705, 400], [0, 471, 705, 16]]

# The Stage Mode epilogue (docs/STORY.md), one (title, lines) per ENDING page.
ENDING_PAGES = [
    ("SERIES \u03a9: CLOSED", ["You walked out of the boardroom with the check.", "The last page of the term sheet gave Omega the board.",
                              "You are rich. You are also an employee.", "", "Win on Difficult to read the last page first."]),
    ("SERIES \u03a9: ON YOUR TERMS", ["You read the last page before you signed.", "Omega was Vesta's and Gigawatt's fund all along.",
                                     "You struck the clause, kept the board and shipped.", "", "The runway is yours."]),
    ("WHERE ARE THEY NOW", ["Blitz is back in a garage, building the next one.", "Dr. Vector published the paper. It cites you.",
                            "Vesta is raising Fund IX.  Moonshot pivoted to quantum.", "Ada's safety report is an industry standard.",
                            "Gigawatt sells you GPUs, at a markup.", "Prompt streamed every fight to ten million followers.",
                            "The Intern got the full-time offer.  Angel is golfing.", "Viral is growth-hacking your launch."]),
    ("BURN RATE", ["A game on the Randori engine.", "Art: Codex CLI image generation.", "Sound and music: synthesized.",
                   "Every founder is fictional."]),
    ("THE END", ["Your runway: infinite.", "Your burn rate: still too high.", "Thanks for playing!"]),
]

# The front sheets: the engine slot (a front bitmap's global) and each frame's
# size, in frame order (sizes the engine's screens place at fixed positions).
SHEETS = {
    "BR_SLOGAN": (0x45119c, [(298, 132)] * 4),
    "BR_ENDING": (0x451190, [(600, 190), (600, 190), (640, 260), (520, 170), (460, 140), (15, 13)]),
    "BR_CLIP1": (0x4511a0, [(794, 37), (496, 80), (282, 119), (304, 126), (363, 123), (291, 27), (291, 27), (256, 26), (256, 26),
                            (256, 29), (334, 108), (334, 108), (151, 26), (151, 26), (304, 38), (29, 19), (29, 19), (29, 19), (37, 19),
                            (70, 19), (70, 19), (110, 19), (102, 19), (45, 19), (37, 19)]),
    "BR_CLIP2": (0x451168, [(704, 353), (494, 23), (494, 23), (469, 41)]),
    "BR_CLIP3": (0x451178, [(334, 108), (305, 213), (210, 22), (238, 24), (275, 23), (275, 24), (188, 23), (165, 23), (304, 156),
                            (126, 21), (186, 21), (235, 21), (279, 22), (228, 22), (111, 19), (304, 10), (429, 6)] + [(63, 26)] * 4
                           + [(63, 21), (279, 22), (279, 22), (132, 41), (176, 41)] + [(29, 40)] * 11 + [(386, 40), (206, 24)]
                           + [(29, 19)] * 3 + [(37, 19), (70, 19), (70, 19), (110, 19), (102, 19), (45, 19), (37, 19)]
                           + [(277, 25)] * 3),
    "BR_CLIP4": (0x45116c, [(713, 332), (40, 45), (235, 111), (171, 38), (173, 38), (52, 19), (47, 20), (59, 24), (59, 24),
                            (543, 332), (282, 239)] + [(15, 19)] * 8 + [(258, 58), (117, 25), (60, 24), (40, 45), (40, 45), (725, 12)]),
    "BR_CLIP5": (0x45117c, [(282, 181), (240, 27), (240, 27), (422, 88), (422, 88), (324, 155), (151, 26), (530, 200)]
                           + [(19, 14)] * 4),
    "BR_CLIP6": (0x4511a4, [(704, 312), (439, 23), (439, 23), (704, 258), (543, 24), (19, 19), (19, 19), (343, 22)]),
    "BR_CLIP7": (0x451188, [(643, 162), (643, 34), (643, 280), (234, 29), (88, 29), (360, 22)] + [(62, 13)] * 4
                           + [(108, 18), (62, 13), (71, 9), (147, 10), (147, 10)]),
}

# --- drawing primitives -------------------------------------------------------
_fonts = {}
def font(path, size):
    key = (path, size)
    if key not in _fonts: _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]

def blank(w, h):
    return Image.new("RGB", (w, h), (0, 0, 0))

def box(img, rect, fill=PANEL, edge=PANEL_EDGE, radius=4, width=1):
    d = ImageDraw.Draw(img); x, y, w, h = rect
    d.rounded_rectangle([x, y, x + w - 1, y + h - 1], radius=min(radius, w // 2, h // 2), fill=fill,
                        outline=edge if edge else None, width=width)

def text(img, s, rect, color=INK, path=FONT_LABEL, size=None, align="center", shadow=True):
    """Fits `s` into rect (x, y, w, h): the largest size that fits, unless given."""
    d = ImageDraw.Draw(img); x, y, w, h = rect
    size = size or max(6, int(h * 0.92))
    while size > 6:
        f = font(path, size); l, t, r, b = d.textbbox((0, 0), s, font=f)
        if r - l <= w - 4 and b - t <= h - 2: break
        size -= 1
    f = font(path, size); l, t, r, b = d.textbbox((0, 0), s, font=f)
    tx = x + (w - (r - l)) // 2 - l if align == "center" else (x + 3 - l if align == "left" else x + w - 3 - r)
    ty = y + (h - (b - t)) // 2 - t
    if shadow: d.text((tx + 1, ty + 1), s, font=f, fill=NEAR_BLACK)
    d.text((tx, ty), s, font=f, fill=color)

def row(w, h, s, hot=False, pad=0):
    """A menu row or a highlight bar."""
    img = blank(w, h)
    if hot: box(img, (0, 0, w, h), fill=HOT, edge=(255, 220, 120), radius=5)
    else: box(img, (0, 0, w, h), fill=(40, 40, 84), edge=None, radius=5)
    text(img, s, (pad, 0, w - 2 * pad, h), HOT_INK if hot else INK)
    return img

def page(w, h, title=None, lines=(), fill=PANEL):
    img = blank(w, h); box(img, (0, 0, w, h), fill=fill, radius=8, width=2)
    if title: text(img, title, (10, 6, w - 20, min(34, h // 3)), (255, 190, 90), FONT_TITLE)
    y = 46 if title else 10
    for line in lines:
        text(img, line, (16, y, w - 32, 20), INK, align="left"); y += 24
    return img

def fit_art(path, w, h, background=NEAR_BLACK, keyed=False):
    """A Codex picture (magenta background) fitted into w×h."""
    img = blank(w, h) if keyed else Image.new("RGB", (w, h), background)
    if not path.exists():
        text(img, path.stem.upper(), (0, 0, w, h)); return img
    src = Image.open(path).convert("RGB"); a = np.asarray(src).astype(int)
    mag = (a[..., 0] > 200) & (a[..., 2] > 200) & (a[..., 1] < 90)
    ys, xs = np.nonzero(~mag)
    if len(xs): src = src.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)); mag = mag[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    s = min(w / src.width, h / src.height)
    nw, nh = max(1, int(src.width * s)), max(1, int(src.height * s))
    src = src.resize((nw, nh), Image.LANCZOS)
    m = Image.fromarray(np.uint8(~mag * 255)).resize((nw, nh), Image.LANCZOS).point(lambda v: 255 if v > 128 else 0)
    arr = np.asarray(src).copy(); arr[arr.sum(axis=-1) == 0] = NEAR_BLACK
    img.paste(Image.fromarray(arr), ((w - nw) // 2, (h - nh) // 2), m)
    return img

def cover(path, w, h, darken=1.0):
    if not path.exists():
        img = Image.new("RGB", (w, h), (30, 24, 60)); return img
    src = Image.open(path).convert("RGB"); s = max(w / src.width, h / src.height)
    src = src.resize((int(src.width * s) + 1, int(src.height * s) + 1), Image.LANCZOS)
    x0, y0 = (src.width - w) // 2, (src.height - h) // 2
    arr = (np.asarray(src.crop((x0, y0, x0 + w, y0 + h))).astype(float) * darken).clip(0, 255).astype(np.uint8)
    arr[arr.sum(axis=-1) == 0] = NEAR_BLACK
    return Image.fromarray(arr)

def keyed_text(w, h, s, color, path=FONT_TITLE):
    img = blank(w, h); text(img, s, (0, 0, w, h), color, path); return img

# --- sheets -------------------------------------------------------------------
def sheet_frames(name, sizes, misc):
    W = lambda i: sizes[i][0]; H = lambda i: sizes[i][1]
    frames = [None] * len(sizes)
    def put(i, img): frames[i] = img
    if name == "BR_CLIP1":
        put(1, fit_art(misc / "logo.png", W(1), H(1), keyed=True))
        for i, s in ((7, "START"), (8, "ONLINE GAME"), (9, "CONTROLS")): put(i, row(W(i), H(i), s, hot=True))
        net = page(W(3), H(3), "ONLINE")
        nb = Image.fromarray(np.asarray(net).copy())
        text(nb, "Your address is shown here", (12, 26, W(3) - 24, 18), DIM, align="left")
        nb.paste(row(291, 27, "WAIT FOR A RIVAL"), (6, 52)); nb.paste(row(291, 27, "CONNECT TO A RIVAL"), (6, 82))
        put(3, nb)
        put(5, row(291, 27, "WAIT FOR A RIVAL", hot=True)); put(6, row(291, 27, "CONNECT TO A RIVAL", hot=True))
        tail = blank(W(14), H(14)); box(tail, (0, 0, W(14), H(14)), radius=6); tail.paste(row(151, 26, "BACK"), (76, 1)); put(14, tail)
        dlg = page(W(4), H(4), "CONNECT"); text(dlg, "Rival's address:", (12, 56, 100, 20), INK, align="left")
        dlg.paste(row(150, 25, "OK"), (20, 89)); dlg.paste(row(150, 25, "CANCEL"), (192, 89)); put(4, dlg)
        put(10, page(W(10), H(10), "WAITING FOR A RIVAL")); put(11, page(W(11), H(11), "CONNECTING"))
        put(12, row(W(12), H(12), "CANCEL", hot=True)); put(13, row(W(13), H(13), "OK", hot=True))
        for i, s in zip(range(15, 18), ("LO", "MID", "HI")): put(i, keyed_text(W(i), H(i), s, INK, FONT_LABEL))
        for i, s in zip(range(18, 25), ("OFF", "SEED", "ANGEL", "SERIES A", "SERIES B", "IPO", "ALL")):
            put(i, keyed_text(W(i), H(i), s, INK, FONT_LABEL))
    elif name == "BR_CLIP2":
        p = page(W(0), H(0), None)
        for r, key in enumerate(("Up", "Down", "Left", "Right", "Attack", "Jump", "Defend")):
            text(p, key, (14, 162 + 22 * r, 120, 20), (255, 190, 90), align="left")
        for c in range(4): box(p, (148 + 139 * c, 61, 105, 91), fill=(14, 16, 36), edge=(70, 70, 110))
        p.paste(row(151, 26, "OK"), (362, 320)); p.paste(row(151, 26, "CANCEL"), (534, 320)); put(0, p)
        put(1, keyed_text(W(1), H(1), "Need help with the controls?", DIM, FONT_LABEL))
        put(2, keyed_text(W(2), H(2), "Need help with the controls?", HOT_INK, FONT_LABEL))
        put(3, keyed_text(W(3), H(3), "SURVIVAL STAGE", (255, 150, 60)))
    elif name == "BR_CLIP3":
        put(0, page(W(0), H(0), None))
        rows = [((45, -2, 210, 22), "VS MODE", 2), ((31, 25, 238, 24), "STAGE MODE", 3), ((13, 52, 275, 23), "CHAMPIONSHIP", 4),
                ((13, 79, 275, 24), "2 ON 2 CHAMPIONSHIP", 5), ((46, 105, 206, 24), "BATTLE MODE", 38),
                ((55, 133, 188, 23), "DEMO", 6), ((68, 188, 165, 23), "QUIT", 7)]
        lst = blank(W(1), H(1)); box(lst, (0, 4, W(1), H(1) - 4), fill=(18, 20, 46, ), radius=10, width=2)
        for (x, y, w, h), s, hot in rows:
            lst.paste(row(w, h, s), (x, max(0, y))); put(hot, row(w, h, s, hot=True))
        put(1, lst)
        put(51, row(277, 25, "REPLAYS")); put(50, row(277, 25, "REPLAYS (OFFLINE)")); put(49, row(277, 25, "REPLAYS", hot=True))
        st = page(W(8), H(8), None)
        for (x, y, w, h), s, hot in [((89, 13, 126, 21), "FIGHT!", 9), ((61, 36, 186, 21), "RESET ALL", 10),
                                     ((37, 61, 235, 21), "RANDOMIZE", 11), ((12, 84, 279, 22), "STAGE:", 12),
                                     ((34, 108, 228, 22), "DIFFICULTY:", 13), ((98, 134, 111, 19), "EXIT", 14)]:
            if s.endswith(":"):
                bar = row(w, h, ""); text(bar, s, (6, 0, 150, h), INK, align="left"); st.paste(bar, (x, y))
                hb = row(w, h, "", hot=True); text(hb, s, (6, 0, 150, h), HOT_INK, align="left"); put(hot, hb)
            else:
                st.paste(row(w, h, s), (x, y)); put(hot, row(w, h, s, hot=True))
        put(8, st)
        cap = blank(W(15), H(15)); box(cap, (0, 0, W(15), H(15)), radius=3); put(15, cap)
        sb = row(279, 22, ""); text(sb, "STAGE:", (6, 0, 150, 22), INK, align="left"); put(23, sb)
        sh = row(279, 22, "", hot=True); text(sh, "STAGE:", (6, 0, 150, 22), HOT_INK, align="left"); put(22, sh)
        line = blank(W(16), H(16)); ImageDraw.Draw(line).rectangle([0, 2, W(16) - 1, 3], fill=PANEL_EDGE); put(16, line)
        for k in range(4): put(17 + k, keyed_text(63, 26, f"TEAM {k + 1}", INK, FONT_LABEL))
        put(21, keyed_text(63, 21, "SOLO", INK, FONT_LABEL))
        put(24, keyed_text(W(24), H(24), "GO!", (255, 200, 60))); put(25, keyed_text(W(25), H(25), "STAGE", (255, 150, 60)))
        for n in range(9): put(27 + n, keyed_text(29, 40, str(n + 1), (255, 200, 60)))
        put(36, keyed_text(29, 40, "-", (255, 200, 60))); put(37, keyed_text(W(37), H(37), "ROUND CLEAR!", (255, 200, 60)))
        for i, s in zip(range(39, 42), ("LO", "MID", "HI")): put(i, keyed_text(W(i), H(i), s, INK, FONT_LABEL))
        for i, s in zip(range(42, 49), ("OFF", "SEED", "ANGEL", "SERIES A", "SERIES B", "IPO", "ALL")):
            put(i, keyed_text(W(i), H(i), s, INK, FONT_LABEL))
    elif name == "BR_CLIP4":
        put(0, page(W(0), H(0), "CHAMPIONSHIP")); put(9, page(W(9), H(9), "BRACKET"))
        put(1, fit_art(misc / "random_face.png", 40, 45)); put(22, fit_art(misc / "random_face.png", 40, 45))
        put(23, fit_art(misc / "random_face.png", 40, 45))
        yn = page(W(2), H(2), None); yn.paste(row(52, 19, "YES"), (44, 70)); yn.paste(row(47, 20, "NO"), (148, 70)); put(2, yn)
        put(3, keyed_text(W(3), H(3), "Shuffle the order?", INK, FONT_LABEL))
        put(4, keyed_text(W(4), H(4), "Is the setting OK?", INK, FONT_LABEL))
        put(5, keyed_text(W(5), H(5), "YES", INK, FONT_LABEL)); put(6, keyed_text(W(6), H(6), "NO", INK, FONT_LABEL))
        put(7, row(59, 24, "YES", hot=True)); put(8, row(59, 24, "NO", hot=True))
        put(10, page(W(10), H(10), None))
        for n in range(8): put(11 + n, keyed_text(15, 19, str(n + 1), (255, 200, 60), FONT_LABEL))
        put(19, keyed_text(W(19), H(19), "UNICORN!", (255, 200, 60))); put(20, keyed_text(W(20), H(20), "AI FOUNDER", INK, FONT_LABEL))
        put(21, keyed_text(W(21), H(21), "TEAM", INK, FONT_LABEL))
        track = blank(W(24), H(24)); box(track, (0, 2, W(24), 8), fill=(60, 60, 100), edge=None, radius=3); put(24, track)
    elif name == "BR_CLIP5":
        panel = blank(W(0), H(0)); box(panel, (0, 0, W(0), H(0)), fill=(18, 20, 46), radius=10, width=2)
        for (x, y, w, h), s in (((14, 13, 256, 26), "START"), ((14, 45, 256, 26), "ONLINE GAME"), ((14, 76, 256, 29), "CONTROLS"),
                                ((16, 107, 240, 27), "REPLAYS & INFO"), ((16, 139, 240, 27), "WEBSITE")):
            panel.paste(row(w, h, s), (x, y))
        put(0, panel)
        put(1, row(240, 27, "REPLAYS & INFO", hot=True)); put(2, row(240, 27, "WEBSITE", hot=True))
        put(3, row(W(3), H(3), "BURN RATE ON GITHUB", hot=True)); put(4, row(W(4), H(4), "BURN RATE ON GITHUB"))
        wait = page(W(5), H(5), "PLEASE WAIT"); wait.paste(row(151, 26, "CANCEL"), (73, 115)); put(5, wait)
        put(6, row(151, 26, "CANCEL", hot=True))
        hlp = page(W(7), H(7), "CONTROLS")
        for b, s in enumerate(("Up", "Down", "Left", "Right", "Attack", "Jump", "Defend")):
            text(hlp, s, (12, 54 + 20 * b, 100, 18), (255, 190, 90), align="left")
        put(7, hlp)
        for i, s in zip(range(8, 12), ("<", "<", ">", ">")): put(i, keyed_text(19, 14, s, HOT if i % 2 else INK, FONT_LABEL))
    elif name == "BR_CLIP6":
        p = page(W(0), H(0), "REPLAYS & INFO")
        for y, s in ((62, "Author:"), (87, "Info:"), (164, "Saved:")): text(p, s, (14, y, 150, 20), (255, 190, 90), align="left")
        text(p, "Record every match", (14, 242, 220, 20), INK, align="left")
        p.paste(row(151, 26, "OK"), (187, 269)); p.paste(row(151, 26, "CANCEL"), (359, 269)); put(0, p)
        put(1, keyed_text(W(1), H(1), "How do replays work?", DIM, FONT_LABEL))
        put(2, keyed_text(W(2), H(2), "How do replays work?", HOT_INK, FONT_LABEL))
        put(3, page(W(3), H(3), "CHALLENGE", ["Beat the AI founders on Difficult."]))
        put(4, keyed_text(W(4), H(4), "More about the challenge", HOT_INK, FONT_LABEL))
        put(5, row(19, 19, "", hot=True)); ck = row(19, 19, "x", hot=True); put(6, ck)
        put(7, keyed_text(W(7), H(7), "Open the replay folder", HOT_INK, FONT_LABEL))
    elif name == "BR_CLIP7":
        body = page(W(0), H(0), "ONLINE FEATURES")
        body.paste(row(234, 29, "ENABLE"), (134, 74)); body.paste(row(88, 29, "NO"), (390, 74)); put(0, body)
        edge = blank(W(1), H(1)); box(edge, (0, 0, W(1), H(1)), radius=6); put(1, edge)
        put(2, page(W(2), H(2), None, ["Burn Rate can check for updates.", "Nothing else is sent."]))
        put(3, row(234, 29, "ENABLE", hot=True)); put(4, row(88, 29, "NO", hot=True)); put(5, row(360, 22, "MORE", hot=True))
        for i, s in zip(range(6, 10), ("OFFLINE", "OFFLINE", "ONLINE", "ONLINE")): put(i, row(62, 13, s, hot=i % 2 == 1))
        put(11, row(62, 13, "...")); put(12, keyed_text(71, 9, "NEWS", DIM, FONT_LABEL))
        put(13, keyed_text(147, 10, "made with Randori", HOT_INK, FONT_LABEL)); put(14, keyed_text(147, 10, "made with Randori", DIM, FONT_LABEL))
    elif name == "BR_ENDING":
        # The epilogue of docs/STORY.md: f0 after Easy/Normal, f1 after
        # Difficult/CRAZY!, then f2-f4 for both.
        for i, (title, lines) in enumerate(ENDING_PAGES): put(i, page(W(i), H(i), title, lines))
        put(5, keyed_text(15, 13, ">", HOT, FONT_LABEL))
    for i, f in enumerate(frames):
        if f is None: frames[i] = page(*sizes[i]) if sizes[i][0] > 40 and sizes[i][1] > 20 else row(*sizes[i], "")
        assert frames[i].size == sizes[i], (name, i, frames[i].size, sizes[i])
    return frames

def pack(frames, width):
    """Shelf packing in frame order; returns the atlas and [x, y, w, h] per frame."""
    rects, x, y, shelf = [], 0, 0, 0
    width = max(width, max(f.size[0] for f in frames))
    for f in frames:
        w, h = f.size
        if x + w > width: x, y, shelf = 0, y + shelf + 1, 0
        rects.append([x, y, w, h]); x += w + 1; shelf = max(shelf, h)
    atlas = blank(width, y + shelf)
    for f, (x, y, w, h) in zip(frames, rects): atlas.paste(f, (x, y))
    return atlas, rects

# --- single pictures ----------------------------------------------------------
def cursor():
    img = blank(11, 19); d = ImageDraw.Draw(img)
    pts = [(0, 0), (0, 15), (4, 11), (7, 18), (9, 17), (6, 10), (10, 10)]
    d.polygon(pts, fill=(255, 200, 80), outline=(60, 20, 10)); return img

def words(color):
    img = blank(256, 258); d = ImageDraw.Draw(img); f = font(FONT_MONO, 13)
    for g in range(32, 127):
        x, y = 16 * (g & 15), 16 * (g >> 4) + 1
        d.text((x + 1, y + 2), chr(g), font=f, fill=NEAR_BLACK); d.text((x, y + 1), chr(g), font=f, fill=color)
    x, y = 16 * (254 & 15), 16 * (254 >> 4) + 1
    d.rectangle([x + 1, y + 5, x + 6, y + 10], fill=color, outline=NEAR_BLACK)
    return img

def frame_cell():
    img = Image.new("RGB", (198, 54), (20, 22, 48)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 197, 53], outline=(70, 64, 120))
    d.rectangle([8, 6, 49, 52], fill=NEAR_BLACK, outline=(110, 100, 170))
    for y, label in ((15, "RUNWAY"), (35, "HYPE")):
        d.rectangle([56, y, 181, y + 11], fill=(10, 10, 24), outline=(90, 84, 140))
        d.text((184, y + 1), label[0], font=font(FONT_LABEL, 11), fill=DIM)   # R / H beside each bar
    d.text((58, 3), "RUNWAY", font=font(FONT_LABEL, 9), fill=DIM); d.text((58, 27), "HYPE", font=font(FONT_LABEL, 8), fill=DIM)
    return img

def bars():
    a = np.zeros((51, 150, 3), np.uint8); x = np.linspace(0, 1, 150)[:, None]
    def grad(c0, c1): return (np.array(c0) * (1 - x) + np.array(c1) * x).astype(np.uint8)
    a[0:10] = grad((40, 120, 255), (120, 220, 255))        # MP ("hype")
    a[10:20] = (30, 34, 70)                                 # MP backdrop
    a[20:30] = grad((40, 190, 90), (160, 240, 90))          # HP ("runway")
    a[30:40] = (110, 40, 40)                                # recoverable HP
    a[40:50] = (240, 255, 220)                              # healing flash
    for r in (0, 20): a[r] = np.minimum(a[r].astype(int) + 50, 255)
    a[a.sum(axis=-1) == 0] = NEAR_BLACK
    return Image.fromarray(a)

def board(w, h, title=None, columns=()):
    img = Image.new("RGB", (w, h), (24, 22, 54)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(255, 132, 40))
    if title: text(img, title, (8, 4, 150, h - 8), (255, 190, 90), FONT_TITLE, align="left")
    for x, s in columns: text(img, s, (x - 8, h - 24, 56, 20), INK)
    return img

def charmenu():
    img = Image.new("RGB", (705, 487), (16, 16, 40)); d = ImageDraw.Draw(img)
    text(img, "PICK YOUR FOUNDER", (0, 2, 705, 30), (255, 190, 90), FONT_TITLE)
    for r in range(2):
        for c in range(4):
            x, y = 107 + 153 * c, 61 + 212 * r
            box(img, (x - 14, y - 22, 148, 206), fill=(30, 30, 66), radius=8, width=2)
            d.rectangle([x - 1, y - 1, x + 120, y + 120], fill=NEAR_BLACK, outline=(110, 100, 170))
    return img

def countdown(n):
    img = Image.new("RGB", (51, 58), NEAR_BLACK); text(img, str(n), (0, 0, 51, 58), (255, 170, 50), FONT_TITLE); return img

def join(bright):
    img = blank(120, 66); box(img, (4, 10, 112, 46), fill=HOT if bright else (60, 40, 90), radius=8)
    text(img, "PRESS ATTACK", (8, 14, 104, 18), HOT_INK); text(img, "TO JOIN", (8, 34, 104, 18), HOT_INK)
    return img

def cmc():
    img = page(365, 103, None); text(img, "HOW MANY AI FOUNDERS?", (10, 8, 345, 40), (255, 190, 90), FONT_TITLE)
    ImageDraw.Draw(img).rectangle([62, 68, 293, 89], fill=(14, 16, 36)); return img

def sparks(misc):
    img = blank(612, 256); src = misc / "sparks.png"
    if not src.exists(): return img
    import process
    a, fg, boxes = process.find_poses(Image.open(src), 8, min_cells=10)
    def place(i, x, y, w, h):
        x0, y0, x1, y1 = boxes[i]; s = min((w - 4) / (x1 - x0), (h - 4) / (y1 - y0))
        rgb, keep = process.render(a, fg, boxes[i], s); kh, kw = keep.shape
        sub = np.asarray(img).copy(); ox, oy = x + (w - kw) // 2, y + (h - kh) // 2
        region = sub[oy:oy + kh, ox:ox + kw]; region[keep] = rgb[keep]; return Image.fromarray(sub)
    for i in range(4):
        img = place(i, 102 * (i + 1), 0, 102, 80)          # heavy hit, frames 1-4
        img = place(i, 61 * (i + 1), 80, 61, 48)           # light hit, frames 6-9
        img = place(4 + i, 102 * (i + 1), 128, 102, 80)    # effect hits, frames 11-14
        img = place(4 + i, 61 * (i + 1), 208, 61, 48)      # light effect hits, frames 16-19
    return img

def backgrounds(misc):
    """MENU_BACK1..13 and the loading backdrop: the title art and darkened stages."""
    sources = [misc / "title.png"] * 5 + [misc / f"stage_{s}.png" for s in ("demoday", "sandhill", "serverfarm", "office")] * 2
    out = []
    for i, src in enumerate(sources[:13]):
        img = cover(src, *SCREEN, darken=0.85 if i < 5 else 0.45)
        d = ImageDraw.Draw(img); d.rectangle([570, 484, 793, 549], fill=(16, 12, 36))
        box(img, (4, 518, 56, 26), fill=(40, 20, 30), edge=(255, 90, 60), radius=5)
        text(img, "QUIT", (4, 518, 56, 26), (255, 140, 110))
        out.append(img)
    wait = cover(misc / "title.png", *SCREEN, darken=0.4)
    text(wait, "LOADING", (40, 230, 714, 80), (255, 170, 50), FONT_TITLE)
    return out, wait

def device_icons(misc):
    src = misc / "icons.png"; icons = []; boxes = None
    if src.exists():
        import process
        try:
            a, fg, boxes = process.find_poses(Image.open(src), 5, min_cells=20)
        except SystemExit:
            boxes = None
    for k in range(5):
        img = Image.new("RGB", (106, 91), (20, 22, 48)); ImageDraw.Draw(img).rectangle([0, 0, 105, 90], outline=(90, 84, 140))
        if src.exists() and boxes:
            x0, y0, x1, y1 = boxes[k]; s = min(96 / (x1 - x0), 80 / (y1 - y0))
            rgb, keep = process.render(a, fg, boxes[k], s); kh, kw = keep.shape
            arr = np.asarray(img).copy(); ox, oy = (106 - kw) // 2, (91 - kh) // 2
            region = arr[oy:oy + kh, ox:ox + kw]; region[keep] = rgb[keep]; img = Image.fromarray(arr)
        icons.append(img)
    # CS2 joystick 1, CS3 joystick 2, CS4, CS5 devices 3-4, CS6 keyboard (icons: keyboard, blue, red, green, yellow).
    return [icons[1], icons[2], icons[3], icons[4], icons[0]]

def road(misc):
    """The engine's built-in road (background 99), returned as back99_1..3:
    back99_2 opaque at (250 − camera/100, 120), back99_3 keyed every 500 px at
    y 175 (0.7 parallax), back99_1 opaque every 320 px at y 390 on the road
    (the engine fills the road 0x575757 and the rails itself)."""
    title = misc / "title.png"
    if title.exists():
        src = Image.open(title).convert("RGB"); s = 794 / src.width; src = src.resize((794, int(src.height * s)), Image.LANCZOS)
        a = np.asarray(src)
        # The burning bill (upper middle) as the far billboard; the skyline band as the tiled mid layer.
        bill = Image.fromarray(a[int(a.shape[0] * 0.06):int(a.shape[0] * 0.36), 220:574].copy()).resize((300, 150), Image.LANCZOS)
        top = int(a.shape[0] * 0.33)
        sky = Image.fromarray(a[top:top + 115, 0:500].copy())
    else:
        bill, sky = Image.new("RGB", (300, 150), (60, 30, 30)), Image.new("RGB", (500, 115), (30, 30, 60))
    lane = Image.new("RGB", (320, 8), (0x57, 0x57, 0x57)); ImageDraw.Draw(lane).rectangle([20, 2, 140, 5], fill=(235, 225, 160))
    out = []
    for img in (lane, bill, sky):
        arr = np.asarray(img).copy()
        if img is bill: arr[arr.sum(axis=-1) == 0] = NEAR_BLACK
        out.append(arr)
    return out

# --- the whole set ------------------------------------------------------------
def build(misc, generated_swift):
    pics, sheets = {}, []
    for name in ("BR_SLOGAN", "BR_ENDING", "BR_CLIP1", "BR_CLIP2", "BR_CLIP3", "BR_CLIP4", "BR_CLIP5", "BR_CLIP6", "BR_CLIP7"):
        slot, sizes = SHEETS[name]
        atlas, rects = pack(sheet_frames(name, sizes, misc), 800)
        pics[name] = atlas; sheets.append((slot, rects))
    pics["BR_CURSOR"] = cursor()
    backs, pics["BR_WAIT"] = backgrounds(misc)
    for i, img in enumerate(backs): pics[f"MENU_BACK{i + 1}"] = img
    for i, img in enumerate(device_icons(misc)): pics[f"BR_DEVICE{i + 2}"] = img
    pics["BR_FRAME"] = frame_cell()
    for i, c in enumerate([(240, 240, 240), (90, 170, 255), (110, 230, 110), (255, 100, 100), (255, 200, 70), (255, 140, 60)]):
        pics[f"BR_WORDS{i}"] = words(c)
    pics["BR_PAUSE"] = keyed_text(84, 23, "PAUSED", (255, 200, 60)); pics["BR_DEMO"] = keyed_text(84, 23, "DEMO", (255, 200, 60))
    pics["BR_BOARD1"] = board(490, 61, "RESULTS", [(121, "KO"), (176, "DMG"), (240, "BURN"), (304, "HYPE"), (377, "LOOT"), (421, "")])
    b2 = board(490, 45); ImageDraw.Draw(b2).rectangle([14, 0, 55, 44], fill=NEAR_BLACK); pics["BR_BOARD2"] = b2
    b3 = board(490, 32); text(b3, "TIME", (370, 4, 56, 24), DIM); pics["BR_BOARD3"] = b3
    pics["BR_BOARD4"] = board(490, 45, "TOTAL")
    for name, s, c in (("BR_WIN_ALIVE", "WIN", (120, 240, 120)), ("BR_WIN_DEAD", "WIN", (80, 150, 80)), ("BR_LOSE_DEAD", "LOSE", (240, 90, 90))):
        img = Image.new("RGB", (53, 11), (20, 22, 48)); text(img, s, (0, 0, 53, 11), c, shadow=False); pics[name] = img
    pics["BR_BARS"] = bars()
    pics["BR_CHARMENU"] = charmenu()
    for n in range(1, 6): pics[f"BR_CM{n}"] = countdown(n)
    pics["BR_CMA"], pics["BR_CMA2"] = join(True), join(False)
    pics["BR_CMC"] = cmc(); pics["BR_RFACE"] = fit_art(misc / "random_face.png", 120, 120)
    pics["BR_SPARK"] = sparks(misc)
    bm = page(705, 487, "BATTLE MODE"); pics["BR_BATTLEMODE"] = bm
    pics["BR_BATTLETROOPS"] = page(300, 420, "TROOPS")
    # The Swift side: names and the sheets' rectangles.
    def lst(xs): return "[" + ", ".join(f'"{x}"' for x in xs) + "]"
    body = ["// Generated by tools/content/interface.py; do not edit.", "import RandoriCore", "",
            "extension BurnRateRules {",
            f"    public static let frontBitmaps: [String] = {lst(FRONT)}",
            f"    public static let interfaceBitmaps: [String] = {lst(IFACE)}",
            f"    public static let menuBitmaps: [String] = {lst(MENU)}",
            f"    public static let warBitmaps: [String] = {lst(WAR)}",
            f"    public static let warModeFrames: [[Int32]] = {WAR_MODE_FRAMES}",
            "    public static let frontSheets: [OriginalBitmapSheet] = ["]
    for slot, rects in sheets:
        body.append(f"        .init(slot: 0x{slot:x}, frames: {rects}),")
    body += ["    ]", "}", ""]
    Path(generated_swift).write_text("\n".join(body))
    for k, v in pics.items():
        a = np.asarray(v.convert("RGB")).copy(); pics[k] = a
    return pics
