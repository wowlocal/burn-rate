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
| G1 | Character pipeline: prompts, Codex sheets, slicer (despill, key, scale, anchor), sheets/mirrors/portraits; Blitz in the game with the full frame set | |
| G2 | The roster to nine fighters, each with stats and one special (projectile objects) | |
| G3 | Stages (backgrounds, layers, shadow) and items | |
| G4 | Interface art: title backgrounds, front sheets, bitmap fonts, character screen, HUD, result and loading screens | |
| G5 | Sound effects and music | |
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

## Next task

E10 in the engine (ntsd-2.4 exp/engine-split): the window title/class, the
title screen's credit lines and links, and the other "LF2" captions become
game values with LF2's as the default (NTSD unchanged); then G1.
