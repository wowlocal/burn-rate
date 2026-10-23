# Burn Rate — story and missions (design)

Design for Stage Mode's campaign, 2026-10-23 (the user's request: "попроси
запроектировать миссии и сюжетку"). It replaces the single set 1-1..1-5 with
six acts. Every name below is fictional; no founder is a real person.
Implemented and checked the same day (G7 in [PLAN.md](PLAN.md)); the HP values
await tuning from real play.

## Premise: the Last Round

Omega Capital, a fund nobody has met, announces **Series Ω**: one check big
enough to end the runway problem forever, and a cluster of a million GPUs
with it. The term sheet goes to the founder who is still standing in its
boardroom on closing day. Every startup in the valley is burning cash.
**Runway** is your health (HP) and **Hype** is your energy for specials (MP).
There are ten founders and one check.

You play any founder. The other nine are your rivals, and so are their
interns. If you pick a founder who also appears as an enemy, the game treats
them as a rival with the same pitch, a mirror match.

## The cast

| Founder | In the story | Where they stand |
| --- | --- | --- |
| Blitz | the hoodie wunderkind the press calls "the next one" | boss of Act 1, the Garage |
| Moonshot | ex-crypto hype bro, owns every Demo Day | boss of Act 2 |
| Vesta | general partner, decides who gets a term sheet | boss of Act 3; on Omega's board |
| Ada | AI-safety lead who wants the race slowed down | boss of Act 4, the Safety Review |
| Gigawatt | compute baron who rents out the GPUs everyone needs | boss of Act 5; on Omega's board |
| Dr. Vector | researcher every lab tries to poach | Acts 2, 4, 5, 6 |
| Prompt | prompt-engineer streamer, broadcasts every fight | Acts 1, 2, 4, 6 |
| Viral | growth hacker, sells hype to the highest bidder | Acts 1, 2, 4, 6 |
| Angel | angel investor, writes small checks and long clauses | Acts 1, 3; on Omega's board |
| Intern | tireless, everywhere, works for whoever pays | every act |

The twist: Omega Capital is Vesta's and Gigawatt's joint fund, with Angel
as its third seat. Series Ω was never meant to fund a winner. It was meant
to buy the last founder standing cheaply: the final page of the term sheet
hands the board to Omega.

## Structure

The engine's Stage Mode plays stage *sets*. The settings screen picks the
first set (Stage 1-6). A set plays its stages in order, x-1, x-2 and so on,
and ends at the first stage ID it does not define. The next set follows,
and after the final set comes the ENDING. Each set has one arena
(`stageBackgrounds`). So:

- **Six acts are the six sets** (stage IDs 0-3, 10-13, …, 50-53). A run
  started on Stage 1 plays the whole story, 24 missions. Starting on a
  later set skips the earlier acts, as in any arcade game.
- **Four missions per act.** x-1 to x-3 are fights in two phases: the
  camera stops at the phase's bound until its enemies fall. x-4 is the
  act's boss. `<boss>` marks the boss, and `<soldier>` escorts keep coming
  until the boss falls.
- **One arena per act**, so the setting changes when the act changes: the
  Garage, Demo Day, Sand Hill Road, the Open Office, the Server Farm and the
  Board Room. Two of these arenas are new: the Garage and the Board Room,
  drawn with Codex CLI like the rest.
- **The final set is Act 6** (`finalStageSet` 50..<60).

Enemy HP in the tables below is the base value. The engine scales it by
difficulty: Easy ×0.75, CRAZY! ×1.5. These are first-pass numbers, to be
tuned from real play.

### Act 1 — Pre-Seed (the Garage)

Everyone starts in a garage. Yours is next door to Blitz's.

| Mission | Name | Beat | Phase 1 | Phase 2 |
| --- | --- | --- | --- | --- |
| 1-1 | Hackathon Night | Blitz's interns come to copy your whiteboard | Intern 120 ×3 | Intern 120 ×2, Prompt 150 |
| 1-2 | Cap Table Brawl | a growth hacker wants 20% for "distribution" | Viral 180, Intern 120 ×2 | Viral 220, Prompt 180 |
| 1-3 | Seed Hunters | the angels arrive, and they bring friends | Angel 200, Intern 120 ×2 | Angel 250, Moonshot 200 |
| 1-4 | **The Wunderkind** | Blitz decides there is room for one garage | **Blitz 600** + Intern soldiers (120 ×2) | |

### Act 2 — Seed (Demo Day)

Your seed round got you three minutes on stage. Everyone wants those three
minutes.

| Mission | Name | Beat | Phase 1 | Phase 2 |
| --- | --- | --- | --- | --- |
| 2-1 | Line for the Mic | the queue for the stage turns into a scrum | Prompt 200, Viral 200 | Intern 130 ×3, Prompt 220 |
| 2-2 | Live Demo | your demo breaks and Dr. Vector says it is his model | Dr. Vector 220, Intern 130 ×2 | Dr. Vector 260, Ada 220 |
| 2-3 | Standing Ovation | the hype has to be taken back | Moonshot 240, Viral 220 | Moonshot 260, Blitz 240 |
| 2-4 | **The Hype Man** | Moonshot owns this room and every room after it | **Moonshot 700** + Viral soldiers (180 ×2) | |

### Act 3 — Series A (Sand Hill Road)

Demo Day bought you meetings. Now get a term sheet.

| Mission | Name | Beat | Phase 1 | Phase 2 |
| --- | --- | --- | --- | --- |
| 3-1 | Cold Intros | the angels guard the partners' doors | Angel 220, Intern 130 ×2 | Angel 250 ×2 |
| 3-2 | Partner Meeting | Vesta brings a "friendly" co-investor | Vesta 250, Angel 220 | Vesta 280, Moonshot 250 |
| 3-3 | Term Sheet Fight | two funds and one allocation | Vesta 280 ×2 | Vesta 280, Angel 250, Intern 130 |
| 3-4 | **The Down Round** | Vesta offers half your valuation, and her fists | **Vesta 800** + Angel soldiers (200 ×2) | |

### Act 4 — Hypergrowth (the Open Office)

The money is in. Now hire a hundred people and ship before anyone else does.

| Mission | Name | Beat | Phase 1 | Phase 2 |
| --- | --- | --- | --- | --- |
| 4-1 | Poaching Season | rivals raid your team at the kombucha tap | Intern 130 ×4 | Intern 130 ×2, Prompt 220 |
| 4-2 | All-Hands | three founders crash your all-hands | Viral 260, Moonshot 260 | Blitz 260, Viral 260 |
| 4-3 | Red Team | Dr. Vector and Ada test your model the hard way | Dr. Vector 280 | Dr. Vector 280, Ada 260 |
| 4-4 | **The Safety Review** | Ada will not let you launch until you beat her | **Ada 850** + Dr. Vector soldiers (220 ×2) | |

### Act 5 — The Compute War (the Server Farm)

You can launch now, but only if you have the GPUs, and Gigawatt has all of
them.

| Mission | Name | Beat | Phase 1 | Phase 2 |
| --- | --- | --- | --- | --- |
| 5-1 | Rack and Ruin | the night shift guards the racks | Intern 140 ×3 | Intern 140 ×2, Dr. Vector 280 |
| 5-2 | Gradient Storm | the researchers fight for the last cluster | Dr. Vector 300 ×2 | Dr. Vector 300, Ada 280 |
| 5-3 | Cooling Failure | Gigawatt sends his muscle, and Blitz is back for more | Gigawatt 400 | Gigawatt 400, Blitz 280 |
| 5-4 | **The Compute Baron** | Gigawatt himself, in front of the main breaker | **Gigawatt 1000** + soldiers Intern 140, Dr. Vector 240 | |

### Act 6 — The Last Round (the Board Room)

Closing day, top floor. Everyone you beat is here, and Omega's board is
waiting.

| Mission | Name | Beat | Phase 1 | Phase 2 |
| --- | --- | --- | --- | --- |
| 6-1 | Proxy Fight | the investors vote with their fists | Angel 300, Vesta 300 | Moonshot 300, Angel 300 |
| 6-2 | Hostile Takeover | the founders you beat team up against you | Blitz 320, Viral 300 | Prompt 300, Blitz 320 |
| 6-3 | Closing Day | the lab joins in, with the baron's blessing | Ada 320, Dr. Vector 320 | Gigawatt 450, Dr. Vector 320 |
| 6-4 | **Series Ω** | Omega's board: Vesta and Gigawatt, together | **Vesta 900**, **Gigawatt 1100** + Angel soldiers (220 ×2) | |

## The ending

The ENDING sheet shows its pages after Act 6. Its first page depends on the
difficulty; pages 3-5 are shared.

| Page | Shown on | Text |
| --- | --- | --- |
| f0 | Easy, Normal | **SERIES Ω: CLOSED.** You walked out with the check. On the last page of the term sheet, Omega takes the board. You are rich, and you are an employee. (Win on Difficult to read the last page first.) |
| f1 | Difficult, CRAZY! | **SERIES Ω: ON YOUR TERMS.** You read the last page before you signed. Omega was Vesta's and Gigawatt's fund all along. You struck the clause, kept the board and shipped. |
| f2 | all | **WHERE ARE THEY NOW.** One line for each founder (below). |
| f3 | all | **BURN RATE.** A game on the Randori engine. Art: Codex CLI image generation. Sound and music: synthesized. Every founder is fictional. |
| f4 | all | **THE END.** Your runway: infinite. Your burn rate: still too high. Thanks for playing. |

Where are they now: Blitz is back in a garage, building the next one. Dr.
Vector published the paper, and it cites you. Vesta is raising Fund IX.
Moonshot pivoted again, this time to quantum. Ada's safety report is now an
industry standard. Gigawatt sells you GPUs at a markup. Prompt has ten million
followers and streamed every fight. The Intern got the full-time offer. Angel
is back on the golf course. Viral is growth-hacking your launch.

## How the player sees the story

The engine has no dialogue or cut-scene slot between stages. Its stage
labels read "STAGE a-b". Phases cannot change the music, because the engine
rejects `music:` in a phase. So the game tells the story through:

- **arenas**: the act's setting changes with the act;
- **line-ups**: who you fight, in what order, and who the boss is
  (the HUD's enemy count and HP make a boss with soldiers obvious);
- **the ENDING sheet**: the epilogue, with a different first page by
  difficulty.

Mission names and beats live in this document and in the README's story
section. A future Randori change could let a game show a line of text per
stage, for example a stage title next to "STAGE a-b". That would be an engine
increment with its own review. It is not part of this design.

## Arenas and the Random pick

The background list keeps its first four entries (Demo Day, Sand Hill Road,
the Server Farm, the Open Office) and adds the Garage (4) and the Board Room
(5). The engine's Random arena draws ordinals 0..count−4 plus the road, so
with six arenas Random covers Demo Day, Sand Hill Road and the Server Farm
(before: Demo Day only). Every arena can still be picked by hand in VS.

`stageBackgrounds` for the six sets: {0: 4 (Garage), 10: 0 (Demo Day),
20: 1 (Sand Hill Road), 30: 3 (Open Office), 40: 2 (Server Farm), 50: 5
(Board Room)}.

## Implementation

1. `tools/art/generate_misc.py`: the jobs `stage_garage` and
   `stage_boardroom`. Archive them at half size into `art/raw/misc`.
2. `tools/content/stage.py`: the two arenas, and the six sets with the
   line-ups above.
3. `BurnRateRules`: `finalStageSet` 50..<60 and the `stageBackgrounds`
   above.
4. `tools/content/interface.py`: the ENDING pages above, with page sizes
   chosen to fit their text.
5. Checks:
   - `tools/playtest.py` runs that start each act from the settings screen;
     every act loads its arena, spawns its line-up and plays with no engine
     boundary;
   - a separate check build with every enemy at 1 HP walks a run from
     Act 1 through Act 6 to every ENDING page. It uses a test switch in
     `stage.py` and is never the shipped content;
   - the smoke check and the existing playtest runs still pass.
