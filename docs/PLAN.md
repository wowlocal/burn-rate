# Burn Rate — plan card

An experimental 2D brawler on the [Randori](https://github.com/wowlocal/randori)
engine: Silicon Valley AI startup founders fight it out. Every fighter is a
fictional archetype, not a real person. All content is original: art is
generated with Codex CLI's image generation and processed by this
repository's scripts; nothing comes from NTSD's or LF2's data.

Started 2026-10-23 at the user's request ("как закончишь с правками давай ты
при помощи движка сделаешь новую экспериментальную игру про silicon valley ai
startup founders fight. ассеты будешь генерировать при помощи codex cli").

## Decisions

- **Engine**: Randori as a git submodule at `Vendor/randori`, a path
  dependency (the engine uses `unsafeFlags`, which version-pinned
  dependencies reject). Swift 6.4, macOS 14+, Swift 5 language mode.
- **Storage**: sources here; builds, caches, generated content packages and
  raw Codex outputs on `/Volumes/NTSD-Builds/tasks/burnrate` (never the
  internal disk or X5). Curated source art (cropped, reduced) is committed.
- **Content pipeline**: Codex CLI (`codex exec -i REF … < prompt`) makes
  magenta-backed sheets → `tools/art` (Python + Pillow, venv on NTSD-Builds)
  slices, scales, despills and keys them to black → the Swift builder
  (`BurnRateContentBuilder`, after the engine tests' synthetic pack) writes
  the eight engine packages, their manifests and `GeneratedIdentity.swift`.
- **Rules**: our own `OriginalGameRules` on the synthetic profile's pattern
  (every LF2 ID role −1 or empty), with our item range, Random candidates and
  no AI special moves; the library value set with our loading labels.
- **Roster**: at least 9 fighters (Random and the Demo draw 8 distinct
  eligible characters beyond catalog ordinal 0).
- **Publication**: nothing is published (no remote) without asking the user.
- **Engine contract**: [ENGINE_CONTRACT.md](ENGINE_CONTRACT.md) (survey of
  what a game supplies).

## Roster (working)

| ID | Name | Archetype | Signature |
| --- | --- | --- | --- |
| 1 | Blitz | hoodie wunderkind CEO | Pitch Deck (thrown slides), Pivot dash |
| 2 | Dr. Vector | ML researcher, lab coat | Gradient Beam |
| 3 | Vesta | VC in a fleece vest | Term Sheet throw, Down Round slam |
| 4 | Moonshot | ex-crypto hype bro | Pump & Dump |
| 5 | Ada | AI-safety lead | Guardrail block, Red Team counter |
| 6 | Gigawatt | GPU-hoarding compute baron | GPU throw, Data Center slam |
| 7 | Prompt | prompt-engineer streamer | Jailbreak combo |
| 8 | Intern | tireless intern | Energy-drink rush |
| 9 | Angel | angel investor, golf attire | Golf swing, Exit Strategy |

## Plan

| ID | Step | Status |
| --- | --- | --- |
| G0 | Scaffold: Randori submodule, package (content, app, headless), the content builder writing the eight packages and the identity from authored sources, placeholder art; a headless start to the title and a scripted VS match against the computer to a knock-out | **done** (2026-10-23) |
| G1 | Character pipeline: prompts, Codex sheets, slicer (despill, key, scale, anchor), sheets/mirrors/portraits; Blitz in the game with the full frame set | **done** (2026-10-23, all nine) |
| G2 | The roster to nine fighters, each with stats and one special (projectile objects) | **done** (2026-10-23: D>A projectile, D^A uppercut; balance open) |
| G3 | Stages (backgrounds, layers, shadow) and items | **done** (2026-10-23: four stages, the coffee item; the built-in road waits for E10's name) |
| G4 | Interface art: title backgrounds, front sheets, bitmap fonts, character screen, HUD, result and loading screens | **done** (2026-10-23; LF2's credit lines wait for E10) |
| G5 | Sound effects and music | **done** (2026-10-23, synthesized) |
| G6 | macOS app (.app on NTSD-Builds), window title, playtest | |

## Ledger

- 2026-10-23: feasibility. Codex CLI 0.160 (`image_generation` stable)
  produced a 12-pose sheet of one character (1448×1086, magenta
  background), then a second sheet from the first as reference with the
  same design; scaled to 66 px tall in 79×79 cells the poses read well
  (a magenta fringe to remove).

- 2026-10-23 G0: the package (BurnRateRules, BurnRateContent with the
  generated identity, BurnRateApp, BurnRateHeadless, BurnRateContentBuilder),
  Randori b3efa7a at Vendor/randori; tools/content/stage.py stages DATs
  (plaintext), sheets from the Codex art (tools/art/process.py: magenta
  edge despill, one scale per fighter from the idle pose, feet at
  (39,77) in 79×79 cells, 40 pictures per sheet), placeholder interface
  pictures, synthesized WAVs and the record; the builder encrypts the DATs
  with the engine's public decoder (no copy of the key), writes the eight
  packages and GeneratedIdentity.swift; tools/build.sh makes BurnRate.app.
  Checks: a headless VS against the computer (Blitz against Vesta, the
  synthetic match's menu inputs) reached the knock-out at body ~1040, the
  result, the epilogue and the menu, wrote `recording\20260101_010000_VS.lfr`
  and played a second match; the AppKit app started and played the same
  start with text drawn. Found: the title screen shows LF2's credit lines
  (engine literals) and the window is titled "Little Fighter 2" — an engine
  change (game-supplied branding) is needed before anything is shown.

- 2026-10-23 G1-G3: Codex drew all nine fighters (sheets A, B, C and a
  portrait each, sheet A as the reference for the rest: 36 images, about
  100 s each) and seven misc images (four stages, projectiles/effects, hit
  sparks, the title). process.py: adaptive grouping (the pose count must
  match), an edge-only despill (purple clothes keep their colour), 109x109
  cells with the feet at (49,104) so raised fists and thrown props fit, a
  height per fighter (Intern 58 ... Gigawatt 76), the HUD picture cropped to
  the face. stage.py: boxes relative to the feet; specials on every
  fighter (D>A: frame 240-242, 150 MP, an opoint spawning the fighter's
  projectile 200+id at frame 100; D^A: frame 250-252, 60 MP, a launching
  uppercut); projectiles (type 3) fly frames 100-139 at dvx 12 and vanish
  (next 1000), with 10/20/30 for the engine's hit transitions; four stages
  (backdrop scaled to 550 px with parallax, a mirrored seamless floor band
  1600 wide, z 322-512). Checks: headless VS runs show the windup, the
  thrown slides crossing the stage and the fighters' fight; the start-of-
  match blink (75 ticks, the engine's spawn invulnerability) explained.

- 2026-10-23 G4: tools/content/interface.py draws every interface slot
  (docs/INTERFACE_SLOTS.md, from a read-only survey of the engine): nine
  front-sheet atlases packed in frame order with the engine's frame sizes
  (title menu, mode list, settings box and their highlights at the engine's
  fixed positions; network, controls, replays, tournament, Stage, War and
  opt-in screens as plain labelled panels), the cursor, 13 menu
  backgrounds (Codex title art and darkened stages, a QUIT corner), the
  loading screen, device icons (Codex), the HUD cell (RUNWAY/HYPE bars),
  BARS, six team-coloured 8x16 fonts (Menlo), result boards, the character
  screen (eight portrait windows), countdown digits, join prompts, the
  Random face (Codex), hit sparks (Codex art in the engine's fixed bands)
  and the engine's built-in road (the burning bill, the skyline, lane
  dashes). It writes GeneratedInterface.swift (names, sheet rectangles,
  War frames) for the rules. Checked in the AppKit app: title, mode list,
  character screen with a computer on Random, settings, a match on the
  road with the HUD.

- 2026-10-23 G5: tools/content/audio.py synthesizes every sound (no
  samples): the 18 common slots by their engine events (hit, block,
  knockdown, landing, dash, effect hits, object strike, freeze, ice, fire,
  armour block; valid blips for the six slots without a caller), the five
  menu sounds (join, OK, cancel, fanfare, round over), the attack swing,
  and eight chiptune loops for the engine's music names (kick/snare/hat,
  triangle bass, arpeggio, a pulse lead from a seeded two-bar motif over a
  minor progression; 128-176 BPM, 22-30 s, 16-bit 22.05 kHz WAV for
  AVAudioPlayer). Checked: levels (music peak 0.78, RMS ~0.11; effects
  peak ≤ 0.98), the AppKit app starts with the packaged tracks.

## Next task

E10 in the engine (implemented, in review): then bump Vendor/randori and set
Burn Rate's branding (window title, credit lines, links, "Highway 101");
G5 sounds and music.
