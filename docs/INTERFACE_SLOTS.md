# Interface slots: what Burn Rate must draw (survey 2026-10-23)

Read-only survey of the Randori engine (at b3efa7a plus E10 work in progress,
as vendored in the NTSD port, https://github.com/wowlocal/ntsd-2.4) and NTSD's profile. `E/` = engine/Sources/RandoriCore,
`R/` = engine/Sources/RandoriRuntime, `D/` = ntsd docs/research. Screen 794×550.
Y = [453da4], Y′ = [45757c] (ad-info y line, normally 0); title-menu base
B = Y+202, mode-list base M = Y+206. COLORREF = 0x00BBGGRR.

Rules: list lengths fixed (24 front, 10 interface, 18 common sounds, 11 menu,
5 menu sounds, 2 War). DIBs: 40-byte header, 24-bit (or 4/8-bit, RLE8),
bottom-up. Colour key #000000 applies only when a draw passes key=1 (key 0
copies opaque, black included): exact black only for transparent areas.
Frame −1 or a bitmap without frames draws whole at (x,y); every frame
rectangle must lie inside the image (the Mac backend drops it silently).
frontSheets rectangles are profile data (we may re-pack atlases); frame
indices, positions and click areas are engine constants. The engine reads
frame widths for War labels and ENDING centring. SPARK's rectangles are fixed
in the engine (E/OriginalMenuResourceLoading.swift:79-104).

## 1. frontBitmaps (24)

| # | NTSD name | Size | Use |
|---|---|---|---|
| 0 | LF2_CURSOR | 11×19 | mouse cursor, whole, keyed, at (min(x,775), min(y+2,535)) |
| 1-7 | MENU_CLIP…CLIP7 | see §2 | sheets |
| 8 | MENU_WAIT | 794×550 | loading backdrop, opaque at (0,0) |
| 9 | SLOGAN | 597×265 | 4 frames 298×132, never drawn |
| 10 | ENDING | 419×552 | Stage-mode ending pages |
| 11 | LF2_CURSOR (2nd) | — | loaded, never drawn |
| 12-16 | CS2-CS6 | 106×91 | CONTROL SETTINGS device icon, opaque, at (194+139p,182); CS6 keyboard, CS2/CS3 joysticks 1/2 |
| 17 | FRAME | 198×54 | HUD cell (§3) |
| 18-23 | WORDS0-5 | 251×257 | bitmap fonts (§3) |

Not in Interface but loaded: MENU_BACK1-13 (`MENU_BACK\(ms%13+1)`, title/mode/
network/settings background, whole, keyed; the mode screen fills 794×550 with
0x122565 first; NTSD's is 809×547). A click at x<63, y≥514 on front screens
quits (nothing drawn there: the backgrounds must show it). Quit is row 7 of
the mode list; the title menu has no QUIT.

## 2. frontSheets (frame → use, position)

**MENU_CLIP** (794×500): f1 496×80 title logo at (155,Y+96) (mode screen 153);
also opt-in dialog (155,y), CONTROL SETTINGS (155,35), RECORDING INFO (155,55),
page 8 (155,75), network (155,105). f7, f8 256×26 title highlights START and
ONLINE GAME at (277,B+13), (277,B+45); f9 256×29 CONTROL SETTINGS highlight at
(277,B+76). Network: f3 304×126 box at (253,222) (IP GDI at 289,251; rows
"Waiting for Opponent" y 274-300, "Connect to Opponent" y 305-330); f14 304×38
tail at (253,335) with Back y 336-361; f5, f6 291×27 row highlights at
(259,274), (259,304); f4 363×123 connect/IP dialog at (219,268) (host GDI at
339,327; OK 239-389, Cancel 411-561, y 357-382); f10 334×108 "Waiting" box at
(236,290) (dots fills 5×12 0x577fd7 at 281+20i, 342); f11 334×108
"Connecting" at (236,290); f12 151×26 Cancel/Back highlight ((580,441)
controls, (403,416) recording, (329,336), (322,361), (411,357) network); f13
151×26 OK highlight ((408,441), (231,416), page-8 (318,382), (239,357));
f15-17 29×19 War strength words; f18-24 (37,70,70,110,102,45,37)×19 War preset
labels 0-6. f0 794×37, f2 282×119 never drawn.

**MENU_CLIP2** (704×444): f0 704×353 CONTROL SETTINGS page at (46,121): four
player columns x=194+139p (105 wide), device box y 182-272, name y≈159, seven
key rows at y 283+22r, OK/Cancel art baked in; f1/f2 494×23 help link
normal/hover at (46,475); f3 469×41 Survival banner at (165,299).

**MENU_CLIP3** (≥793×592): f0 334×108 network notice box at (230,221) (GDI
"Waiting for opponent..." at 271,295). f1 305×213 mode list at (244,M): rows
VS Mode, Stage Mode, Championship (1 on 1), 2 on 2 Championship, Battle Mode,
Demo, (row 6 drawn separately), Quit; row 6 = f51 (normal) / f50 (greyed when
networked), 277×25 at (257,M+160). Mode highlights (opaque): row0 f2 210×22
(289,M−2); row1 f3 238×24 (275,M+25); row2 f4 275×23 (257,M+52); row3 f5
275×24 (257,M+79); row4 f38 206×24 (290,M+105); row5 f6 188×23 (299,M+133);
row6 f49 277×25 (257,M+160); row7 f7 165×23 (312,M+188). Settings box: f8
304×156 at (3,3) + f15 304×10 at (3,159); rows Fight!, Reset All, Randomize,
Background, Difficulty, Exit; highlights f9 126×21 (92,16), f10 186×21
(64,39), f11 235×21 (40,64), f12 279×22 (15,87), f13 228×22 (37,111), f14
111×19 (101,137); Stage mode: f23 279×22 replaces Background, f22 its
highlight; values GDI at (174,91), (174,115). Team tournament: f16 429×6
line, f17-20 "Team 1-4" 63×26, f21 63×21. Stage banners: f25 176×41 "Stage"
at (265,299); digits f27+n (n+1) 29×40 at (460,299), (520,299); f36 separator
(490,299); f24 132×41 flashing "GO" at (660,299); f37 386×40 set-clear at
(215,298). f26, f39-48 never drawn.

**MENU_CLIP4** (≥732×598): f0 713×332 tournament entry board at (27,106)
(engine fills 131×41 at 47,384); f9 543×332 bracket board at (119,126); f1
40×45 small Random face; f22, f23 40×45 War units 10, 9; f2 235×111 Yes/No box
at (278,162); f3 171×38 "Shuffle the order?" and f4 173×38 "Is the setting
ok?" at (314,179); f5 52×19 Yes (322,232), f6 47×20 No (426,232); f7/f8 59×24
Yes/No highlights (319,229), (420,230); f10 282×239 player-assign/champion box
at (10,10) (portrait at 90,49); f11-18 15×19 digits 1-8 at (169,24); f19
258×58 champion banner (23,175); f20 117×25 "Computer" (93,22); f21 60×24
"Team" (109,22); f24 725×12 playback track (67,534). Bracket progress = fills
(white, 0x102860, 0xffa0a0) from tables at 0x44d120/0x44d158.

**MENU_CLIP5** (794×600): f0 282×181 title menu panel at (263,B), click rows
(x 276-520, y relative to B): START 15-39, ONLINE GAME 45-70, CONTROL SETTINGS
77-102, RECORDING INFO 107-132, OFFICIAL WEBSITE 137-162; f1/f2 240×27
highlights RECORDING INFO and website at (279,B+107), (279,B+139); f3/f4
422×88 forum banner hover/normal, opaque, at (368,449); f5 324×155 wait dialog
at (258,205) (dots at 284+20i, 290); f6 151×26 Cancel highlight (331,320); f7
530×200 controls-help overlay at (5,39) (GDI key names at 130+108s,
93+20b); f8/f9, f10/f11 19×14 ad-panel arrows.

**MENU_CLIP6** (≥786×697): f0 704×312 RECORDING INFO page at (44,147)
(bitmap-font fields at x 213: y 209, 234 (4 lines), 311; checkbox (287,389):
f5 hover, f6 ticked, 19×19; f7 343×22 folder link (389,388); f1/f2 439×23 help
link (44,461); OK/Cancel baked in); f3 704×258 page 8 "Challenge" at (44,167),
f4 543×24 its link (96,348).

**MENU_CLIP7** (713×540): opt-in dialog at (75,y+100): f0 643×162 body, f3
234×29 Enable highlight (209,y+174), f4 88×29 Disable (465,y+174), f5 360×22
"more" (202,y+240), f1 643×34 bottom edge, f2 643×280 expanded text; f6-f9
62×13 online toggle at (725,5) off/hover/on/hover, f11 busy; f12 71×9 label
above ad tiles; f13/f14 147×10 "advertise" link hover/normal at (0,535).

**ENDING** (419×552): pages f0-4 opaque, centred at ((800−w)/2, (520−h)/2)
(Easy/Normal 0,2,3,4; Difficult/CRAZY 1,2,3,4); f5 15×13 blinking next mark.
**SLOGAN**: never drawn.

## 3. FRAME, fonts, sparks

FRAME: 8 cells at (198·(c&3), 54·(c>>2)), opaque, every tick; team glyph 254
at (5,0), small portrait at (9,7), HP area 57-181 × 16-26, MP 57-181 × 36-46.

WORDS0-5: glyph g = (16·(g&15), 16·(g>>4)+1, 8, 16), keyed, ≥248×257; advance 8
(HUD/summary 9); recording/playback text drawn 4 times offset (bold look);
bytes ≥0x80 draw the whole sheet (keep ASCII); `_` from WORDS0 is the cursor.
WORDS0: mode label "VS mode (Normal)" at x=790−8·len, y 531/510, playback
fields, lives, team-less labels. WORDS1-4: team 1-4 labels, glyph 254, "P1"-
"P8"/"Com" (WORDS1/2 also War labels). WORDS5: "Com" above Stage enemies.

SPARK = menuBitmaps[10] (612×256, keyed), fixed rectangles: frames 1-4 (102i,
0, 102×80) heavy hit (fall > 60); 6-9 (61(i−5), 80, 61×48) light; 11-14
(102(i−10), 128, 102×80) effect:1 heavy (half speed); 16-19 (61(i−15), 208,
61×48) effect:1 light. Anchors (−51,−40) large, (−30,−24) small. Only kind-0
hits spark.

## 4. interfaceBitmaps (10)

0 PAUSE 84×23 at (360,288) keyed; 1 DEMO 84×23 at (360,288); 2 SCORE_BOARD1
490×61 summary header at (150,top), top = (530 − (45N+93) [+45 Battle])/2,
column titles over x 271/326/390/454/527 (Kill, Attack, HP Lost, MP Usage,
Picking) and status x 571; 3 SCORE_BOARD2 490×45 row per player at
(150,top+61+45k) (portrait at board (15,0), name y 15); 4 SCORE_BOARD3 490×32
footer (time at board 430,6); 5 SCORE_BOARD4 490×45 Battle totals; 6-8
WIN_ALIVE, WIN_DEAD, LOSE_DEAD 53×11 row tags at (571,row+15) opaque; 9 BARS
150×51 opaque: rows 0-9 MP, 10-19 MP backdrop (fixed 124 px), 20-29 HP, 30-39
recoverable HP (drawn first), 40-49 healing flash (even ticks); width
31·v/125 (124 px at 500), pixel (0,20) also the low-HP drop.

## 5. menuBitmaps (11), warBitmaps (2)

Seat layout X=153·(seat%4), Y=212·(seat/4). 0 CHARMENU 705×487 opaque at
(40,33): 8 boxes, 120×120 portrait windows at image (107+153c, 61+212r), text
lines at image y 186/208/230 are GDI. 1-5 CM1-5 51×58 countdown digits at
(181+X,125+Y). 6, 7 CMA, CMA2 120×66 "press to join" blink at (147+X,120+Y). 8
CMC 365×103 "how many computer players" at (218,215), keep 62-293 × 68-89
clear. 9 RFACE 120×120 Random portrait at (147+X,94+Y). 10 SPARK (§3). War: W0
BATTLEMODE 705×487 (frames [0,0,705,400] and [0,471,705,16] in popups), W1
BATTLETROOPS troop popup.

## 6. GDI text (host font; no art)

Credit lines (591, Y′+491/511/531) 0xd07750 on 0x602010 (white on hover);
help key names; control-settings names/keys; network IP and messages;
"Loading files" (608,60); settings values, difficulty names, "Music: …" and
"(Press Left/Right to change)" (603,3/20); character select name rows (177+X,
219+Y), character name/" Random" (177+X,241+Y), team line (167/187+X,263+Y);
tournament and War labels; summary numbers and time; Stage "STAGE q-r" lines;
Demo "Press F4 or 'Attack' to exit"; "Volume: %d" and recording notices at
(3,531); a debug line at (0,30) under FRAME.

## 7. panelFrames (11)

Online ad/news panel: needs `sprite\sys\ad%d.bmp` via adinfo (the Mac runtime
throws if reached); leave it out.

## 8. commonSounds (18)

0 hit (no knockdown); 1 blocked; 2 hit with knockdown; 3, 4, 5, 8, 9, 10 no
engine caller (must still be valid WAVs); 6 body hits the ground; 7 dash start;
11 effect:1 hit (+#0); 12 effect:1 knockdown (+#2); 13 held object 100 strikes
type 4/6; 14 freeze; 15 ice breaks; 16 catch fire; 17 blocked on an armoured
ID. All 18 must load.

## 9. menuSounds (5)

0 join/pick/confirm; 1 click/OK/mode confirm/settings/GO tick; 2 back/cancel;
3 cheat 1, stage-set clear, champion; 4 cheat 2, round over, game over.

## Checklist

13 MENU_BACK (~794×550, quit corner x<63 y≥514), MENU_WAIT 794×550, cursor
11×19, the seven MENU_CLIP atlases (logo, title panel + highlights, mode list
+ 8 highlights + playback rows, settings box + highlights + Stage variant,
control-settings and recording pages with OK/Cancel, network boxes, Yes/No,
tournament boards and digits, Stage banners/digits/GO, War words, opt-in
dialog, toggle, playback track), optional ENDING, CS2-CS6 106×91, FRAME
198×54, BARS 150×51, WORDS0-5 251×257 (ASCII + 254), the 10 interface images,
the 11 menu images (CHARMENU 705×487, CM1-5, CMA/CMA2, CMC, RFACE, SPARK
612×256 fixed bands), BATTLEMODE/BATTLETROOPS, 18 common and 5 menu WAVs.
