# Randori engine contract for a new game (survey 2026-10-23)

Read-only survey of engine/ at Randori 3dc22e4 (+ E9 b3efa7a). Path prefixes:
C/ = engine/Sources/RandoriCore/, R/ = RandoriRuntime/, M/ = RandoriMacPlatform/,
A/ = RandoriAppKitHost/, H/ = RandoriHeadlessHost/, S/ = engine/Tests/RandoriTests/Synthetic/,
ev/ = ntsd docs/evidence/, N/ = ntsd native/.

Proven by the synthetic pack: loading, startup → title → START → mode screen, a VS
match vs a computer to KO (body 299), result screen, back to character screen, replay
write/read, text via a glyph source. NOT exercised: Stage, Championship, War, Demo,
network, AppKit host on synthetic content, missing-mirror fallback, frames
80/85/102/111/112/213/214/218.

## 1. Content layout

Root: in a .app `Contents/Resources/<Package>/`; else `--resources DIR` (Bundle(path:));
else the game's fallback bundle (Bundle.module) (R/OriginalRuntimeSession.swift:157-161,
C/OriginalContentLocation.swift:19-24). A plain folder works as a bundle.

Eight package folders (engine constants): OriginalStartup, OriginalCatalog,
OriginalCommonSounds, OriginalLoadingInterface, OriginalCharacterMenu, OriginalWarMenu,
OriginalMatchArenas, OriginalMusic. Folders must hold EXACTLY their manifest's files
(.DS_Store / ._* break loading). Every manifest's SHA-256 = the identity's digest;
every manifest's exeSHA256 = identity.exeSHA256.

- OriginalStartup: manifest.json `{version:1, globalAddress:4509696, globalCount:50088,
  exeSHA256, absentFiles:[…], entries:[{path,count,sha256}]}`; initial.bin (0xc3a8 bytes),
  initial.mask (0xc3a8 × 0x01); bitmaps/<NAME>.dib raw DIBs (BITMAPINFOHEADER first, no BM):
  MENU_BACK1..13 (picked timeGetTime%13+1) and each distinct name in interface.frontBitmaps;
  data/control.txt, data/adinfo.txt, the 5 interface.menuSounds WAVs (names start `data\`);
  absentFiles e.g. ["data/ad0.txt"]. (C/OriginalApplicationStartupInputs.swift)
- OriginalCatalog: manifest `{version:1, exeSHA256, entries:[{name,kind,path,count,sha256}]}`,
  name = Windows path (`data\x.dat`), path = package-relative; kinds file|bitmapFile (BMP with
  header)|dib|music; counts per kind = identity.catalog.files/bitmaps/music; manifest ≤ 2 MiB.
  Needs data\data.txt (file), data\stage.dat (file, encrypted), every object/background DAT,
  every frame sound WAV and weapon sound, every sheet + `_mirror.bmp`, each character's head:
  and small:, each background shadow: (bitmapFile), built-ins shadow1, back99_1..3 (dib in
  the synthetic pack), the 8 `bgm\*.wma` names (music; bytes never read — placeholder text ok).
- OriginalCommonSounds: entries {name,count,sha256}, names = interface.commonSounds (18) in
  order; file = name.dropFirst(5) at package root.
- OriginalLoadingInterface / OriginalCharacterMenu / OriginalWarMenu: entries
  {name, path=name+".dib", count, sha256}; names = interfaceBitmaps (10) / menuBitmaps (11) /
  warBitmaps (2). War menu is always loaded (required even VS-only).
- OriginalMatchArenas: entries {name, path, bytes, sha256} (key `bytes`); name = path with
  backslashes; BMP files: each background's shadow and every layer: BMP (shadow in both
  catalog and arenas).
- OriginalMusic (not in identity): `{sampleRate, entries:[{name:"bgm\\main.wma", resource,
  frames}]}`; AppKit plays with AVAudioPlayer (any AVFoundation format); headless needs
  sampleRate > 0 and frames; SDL/Android/Web decode CAF+ALAC 16-bit only. Missing → startup stops.

Engine-fixed names: package folders, data\data.txt, data\stage.dat, MENU_BACK1..13,
shadow1, back99_1..3, built-in backgrounds 99 "Lee On Road" (2400 wide, z 350–470) and 100
"Random", bgm\main|stage1..5|boss1|boss2.wma, data\control.txt, data\adinfo.txt,
data\ad%d.txt, sprite\sys\ad%d.bmp, `_mirror.bmp`, replays recording\YYYYMMDD_HHMMSS_VS.lfr,
window title "Little Fighter 2" / class "Marti", list lengths 24/10/18/11/2/5, record
address/size. Game-chosen: every name in rules.interface, all DAT/data.txt paths, IDs,
music resource names, identity strings.

Bitmaps: DIB = 40-byte BITMAPINFOHEADER, planes 1, 4/8/24-bit BI_RGB or 8-bit RLE8, ≤ 16.7M
px, image-size 0 or exact. BMP: bfSize = file size, reserved 0, offset ≥ 54. Transparent =
pure black (0,0,0) only. No stretching; rectangles outside the surface are silently dropped
(71–77% of synthetic draws!). A bitmap with no rectangle table draws whole. Screen 794×550.
HUD (C/OriginalWorldHUD.swift:86-116): FRAME panel (front slot 17) per player at
((cell&3)*198, (cell>>2)*54), small portrait at +9,+7, BARS rows y 0/10/20/30/40 (10 px),
width value*31/125 (124 px at 500), at +57,+16 and +57,+36; team mark = team font frame 254
at +5,+0. NTSD sizes: PAUSE/DEMO 84×23; SCORE_BOARD1 490×61; SCORE_BOARD2/4 490×45;
SCORE_BOARD3 490×32; WIN_ALIVE/WIN_DEAD/LOSE_DEAD 53×11; BARS 150×51; CHARMENU 705×487;
CM1–5 51×58; CMA/CMA2 120×66; CMC 365×103; RFACE 120×120; SPARK 612×256; MENU_CLIP 794×500;
MENU_BACK1 809×547 (docs/research/INITIAL_INTERFACE.md, MENU_RESOURCES.md,
MENU_PANEL_BITMAP.md). head: ~120×120 (character-screen face slot); small: ~40×45 (37×41 ok).
Sprite sheets: cells (w+1)×(h+1), `row` columns × `col` rows, picture i at
x=(i%row)(w+1), y=(i/row)(h+1); ≤ 500 pics/sheet, ≤ 10 sheets/object, numbered across
sheets, sheet path < 40 bytes (C/OriginalObjectLoader.swift:204-224,324-367). Ship
`_mirror.bmp` (whole sheet flipped L-R).

Fonts: GDI text from the host (AppKit system bold 13 px; headless = empty masks). Bitmap
fonts = front bitmaps 18–23 (WORDS0–5): 256 glyphs, glyph g at x=(g&15)*16, y=(g>>4)*16+1,
8×16 → image ≥ 248×257. Style 0/1/2 → fonts 18/19/20; teams 1–4 → 19/20/21/22.

Sounds: RIFF/WAVE PCM (tag 1), 8/16-bit, mono/stereo, any rate. 18 common sounds by slot
(guard = 1, armoured guard = 17, heavy-weapon hit = 13; NTSDProfile.swift:18-21 hints).

control.txt (C/OriginalSettingsLoading.swift:107-128): 4 lines × 11 ints (device 0=keyboard,
VK up/down/left/right/attack/jump/defend, 3 joystick buttons); a line of 4 names (backtick =
space); %d → update-check (0 or 2 = nothing); %d → replay recording flag; 2 text lines.
Arrows = VK 0x25–0x28. adinfo.txt: `dont_update 0 5 <end>` + absentFiles ["data/ad0.txt"].

## 2. DAT format

Encoding (C/OriginalDATDecoder.swift): private 37-byte key; byte = v &- key[i%37], i from
file start; first 123 bytes skipped header (key still advances). Decrypted: names ending
`dat`; data\stage.dat always; data.txt never. Encrypt without the key via public API:
`OriginalDATDecoder.decode(zeros(123+N), fileName:"x.dat", translation:.raw)` gives
`0 &- key[...]`, so cipher = plain &- that (untested). Ciphertext must contain no 0x1a and no
CR LF (text mode) — pad whitespace and re-encrypt. Plaintext: no NUL/0x1a, Latin-1, end with
≥ 2 whitespace chars.

data.txt: `<object> id: N type: T file: PATH <object_end>` (≤ 500), `<background> id: N
file: PATH <background_end>` (≤ 99). Catalog ordinal = order; ordinal 0 never a Random candidate.

Object header `<bmp_begin>…<bmp_end>`: name: (<60), head: (<40, required), small: (<36,
required), file(a-b): PATH w: h: row: col: (≥ 1); walking_frame_rate, running_frame_rate
nonzero; 16 doubles: walking_speed(z), running_speed(z), heavy_walking_speed(z),
heavy_running_speed(z), jump_height/distance/distancez, dash_height/distance/distancez,
rowing_height/distance (synthetic values S/SyntheticContentPack.swift:206-210). Weapons:
weapon_hp, weapon_drop_hurt, weapon_hit/drop/broken_sound, <weapon_strength_list>.
Types: 0 char, 1 light weapon, 2 heavy, 3 projectile, 4 throwable, 6 drink, 5 nothing special.

Frames: `<frame> N name` (N 0..399, name ≤ 27) … `<frame_end>`. Scalars pic state wait next
dvx dvy dvz hit_a hit_d hit_j hit_Fa hit_Ua hit_Da hit_Fj hit_Uj hit_Dj hit_ja mp centerx
centery. opoint: kind x y action dvx dvy oid facing; bpoint: x y; cpoint: (long); wpoint:
kind x y weaponact attacking cover dvx dvy dvz. itr: kind x y w h dvx dvy fall arest vrest
respond effect catchingact caughtact … bdefend injury zwidth (≤ 5); bdy: kind x y w h (≤ 5).
sound: paths ≤ 19 chars (cache stride 20). wait+1 ticks; next 0 holds; negative next flips;
999 → 0 (or 212 airborne); ≥ 400 deletes. dv > 500 sets velocity to value−550. MP costs
apply while 0x44d034 ≠ 0 (match prep sets 1).

Engine-selected frames: stand 0–3; walk 5–8; run 9–11; heavy walk/run/stop 12–15/16–18/19;
attack 60 or 65 (random); 70 after kind-6 itr; weapon attacks 20/25/30/35/40/45/50/52/55;
air attack 80; run attack 85; dash attack 90; run-defend 102; defend 110; blocked 111; guard
broken 112; jump 210/211/212 (velocity on 212); dash 213/214 (reverse 216/217); stop run 218;
landing 215 (after 212/state 6) else 219; 94 from state 100; falling 180–183 front, 186–189
back, bounce 185/191; recovery 100/108; lying 230/231; injured 220, 222/224, 226; frozen 200;
burning 203/205; pick-up 115/116 (itr kind 2 only). Items: 0 (spawn at y −500), 60 ground,
70 landed, 7, 20 heavy, 40 types 4/6.
States: 0 stand, 1 walk, 2 run, 3 attack, 4 jump, 5 dash, 6 rowing, 7 defend, 8 broken
guard, 9 catching, 10 caught, 11 injured, 12 falling, 13 frozen, 14 lying, 15 crouch/landing,
16 dazed, 17 drinking, 18/19 burning, 1000/1001/1002/1004 light item, 2000/2004 heavy,
3000/3005/3006 projectiles, 9997 no shadow, 9998 delete.
Absent frames: not drawn, no bdy, hold forever (missing 219 = invisible after landing).
Proven synthetic frame set: 0–3, 5–8, 9–11, 60/61 (+65/66), 110, 180–191, 210–212, 215, 219,
220, 222–227, 230/231 (one bdy each except lying; centerx 12 centery 31). Add for real play:
65 everywhere, 80, 85, 102, 111, 112, 213, 214, 218, 100, 108 (90 if state 5 used). Items:
0–3 (state 1000), 60 (1004), 70.
AI (C/OriginalCharacterAI.swift): type-0 in slots 10–399 (computer seat s → slot s+10);
nearest enemy HP>0 not lying; walks if > 60 away, aligns z within 3, attacks within 80;
defends vs states 3/3xx; random jumps. Punch reach should cover 60 (synthetic: itr x 16 w 56).

Background DAT: name: (≤ 29, _ → space), width:, zboundary: z1 z2, shadow: path label x y,
layer: path transparency width x y height loop … layer_end (≤ 30). stage.dat: `<stage> id:
… <phase> bound: … <phase_end> <stage_end>` — needed even VS-only.

## 3. Code the game supplies

OriginalGameRules.init(profile:reflection:armour:interaction:impact:items:roster:modes:
physics:drawing:effects:lifecycle:fusion:weaponBreak:interface:characterAI:
characterAISpecial:library:) — all public. `.lf2(...)` gives LF2 2.0a ID roles (avoid its
IDs: reflection 200,203,205–207,215,216,209,8,213; armour 6,37,52,124,208,214,220–222; items
100..<200, drinks 122/123; hidden 30–39,50–59; Random < 30; fusion 7+8→51; weapon breaks
100,101,120–124,150,151,201,213,217,218 + 999; effects 998,999,211,219,223–225; AI specials
1,2,4–11,32–36,38,39,50–52). Recommended: own rules on the synthetic profile pattern (all −1
/ empty), itemRange with ≥ 1 item, randomCandidates covering our characters, NoSpecialMoves
(redefine; tests' version internal), deathParticles/fireParticles real IDs if freezing/burning.
Interface: 24 front bitmaps, frontSheets (first 11 slots, ≤ 500 frames, [x,y,w,h]), 10
interface bitmaps, 18 common sounds, 11 menu bitmaps, 2 War bitmaps, 5 menu sounds,
panelFrames, warModeFrames; engine draws fixed frame indices at fixed positions (START row x
276–520 C/OriginalMainMenu.swift:154-166; MENU_CLIP7 frames 3/4 fixed).
library (required, else OriginalLibData.Required): OriginalLibData(loadingLabels:
.init(belowTwo:, fiveToSeven:, others:)); turns on lib.dll behaviours.
initial.bin: zeros except 0x44d78c/0x44d790 = 794/550, 0x44d068 ≠ 0, 0x44d05c = 1,
0x44d020 = 10, 0x44d07c ≠ 0, 0x44dce8 = 0x44a2b4, 0x44d03c > −99 (version), 0x44d010 = 1
(music on, inference). Difficulty 0x450c30.
Identity: OriginalContentIdentity(exeSHA256:catalog:.init(manifestSHA256:entries:files:
bitmaps:music:), startup:.init(manifestSHA256:entries:absentFiles:), loadingManifestSHA256:
interfaceManifestSHA256:menuManifestSHA256:warMenuManifestSHA256:arenaManifestSHA256:rules:);
exeSHA256 any string used consistently; generate digests at build time.
OriginalGameIdentity(name:, userDataFolder:) (~/Library/Application Support/<folder>);
OriginalGame(identity:, content: { OriginalContentLocation(appBundle:$0, identity:,
fallback:{ Bundle.module }) }). Window title fixed "Little Fighter 2" (engine change needed or
retitle NSWindow). Engine still NTSD-named: user default `NTSDOriginalWindow`, headless temp
prefix `ntsd-headless-`.

## 4. App

`RandoriAppKitHost.run(arguments:game:) -> Never`; `RandoriHeadlessHost.run(arguments:game:
defaultMusicDirectory:)`. Path dependency only (unsafeFlags); Swift 6.4; platforms macOS 14;
swiftLanguageModes [.v5]; no RANDORI_PORTABLE on macOS. .app: Contents/Resources/<Package>/,
Info.plist, ad-hoc codesign (N tools/build-native.sh, tools/package_assets.py). Headless needs
--script, --virtual-clock BASE STEP, --no-network; options --resources, --loaded-script,
--exit-after-startup, --body-frame-digests, --exit-after-bodies N, --summary-json, --overlay,
--mute-*, --synchronous-render (synthetic args S/SyntheticHeadlessStartTests.swift:69-73).
Internal (unusable from another package): engineTests, NoSpecialMoves,
OriginalDATDecoder.byte/encrypted, OriginalConcurrentInputs.hex, OriginalIDSet.contains.

## 5. Pitfalls

1. ≥ 1 item in itemRange (else "Source state unknown: no item candidate").
2. Random draws distinct type-0 characters (ordinal ≥ 1, in randomCandidates) for every
   Random seat; Demo draws 8 → need ≥ 9 characters (≥ 8 eligible) for Demo/Random safety.
3. library mandatory. 4. Record words exact (0x44d020 = 10, 0x44d05c = 1).
5. Undersized art silently dropped. 6. Headless frames have no text.
7. Missing frames → invisible/unhittable; frame rates nonzero. 8. head:/small: required.
9. DAT text rules; sound paths ≤ 19. 10. No extra files; don't stage on ExFAT.
11. LF2 ID roles bite. 12. War menu package and stage.dat mandatory.
13. Window title/class fixed; OriginalMusic mandatory on Mac. 14. START y depends on 0x453da4.
