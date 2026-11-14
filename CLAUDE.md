# Kettlebell Timer: handover for Claude Code

A phone-first web app for timed kettlebell circuits. It's for Jass, who trains at home with **one 10 kg kettlebell**, aiming to **build muscle and lose fat**. It's built as a single static page with no framework, no build step and no backend.

- **Live site:** https://jass-kettlebell-timer.netlify.app (Netlify site `jass-kettlebell-timer`, site ID `43e712c6-151f-4f07-b390-dfb02e3588cd`)
- **Used on:** an Android phone in Chrome, installed to the home screen, propped on the floor during workouts.
- **About Jass:** prefers direct, honest feedback and detailed step-by-step technical guidance with nothing assumed.

## Files

| File | What it is |
|---|---|
| `index.html` | The whole app: CSS, markup and JS in one file, about 930 lines |
| `manifest.webmanifest` | Settings that make it installable: name, icons, full screen, portrait |
| `sw.js` | Service worker for offline use. Fetches from the network first and falls back to its cache. Its cache name is `kb-v6`. It also precaches the font files, so the app looks right offline |
| `fonts/` | Self-hosted Barlow and Barlow Condensed (Latin subset, woff2), with the font licence in `OFL.txt` |
| `icon-192.png`, `icon-512.png` | App icons: an orange kettlebell on dark `#101216` |
| `netlify.toml` | Netlify settings: publish the repo root, no build, never cache `sw.js`, and security headers (CSP, nosniff, no referrer, permissions policy) for every file, and a one-year cache for `fonts/` |
| `tests/` | Playwright checks (see Testing) |

## Requirements agreed with the user (don't change without asking)

- **Workout length:** 10 / 15 / 20 / 30 / 45 minutes, **including** the warm-up and cool-down. Every combination must come out at exactly the chosen length.
- **Focus:** Full body / Legs / Upper body / Core.
- **Work/rest presets:** 30/30, 40/20 (default), 45/15, 50/10, or custom (work 15–120 s, rest 5–90 s, in 5 s steps).
- **Rest between rounds:** adjustable at 30 / 45 / 60 (default) / 90 / 120 s.
- **Structure:** circuits of moves repeated for rounds, with a 3-round target. 10 and 15-minute workouts usually come out at 2 rounds.
- **Difficulty:** Standard / Hard (default) / Brutal. The user found the original workouts too easy and asked for progressive rounds and compound moves.
  - **Standard:** the same moves every round, no complexes.
  - **Hard:** each round swaps a move for the next rung of its ladder (for example goblet squat → one-and-a-half squat → goblet thruster), ending on complexes where the ladder reaches one.
  - **Brutal:** starts one rung up, climbs every round, and can pick complexes as the opening move.
- **Complexes:** several moves chained without putting the bell down, such as "Clean, squat, press". They take one normal slot.
- **Voice during complexes:** a setup switch between **Move by move** (default: the voice calls each step in time with the figure) and **Name once** (the complex is only named in the rest before it).
- **Finisher:** on by default, with an On/Off setting. All-out 20 s on / 10 s off just before the cool-down: 4 rounds at 15 min, 6 at 20 min, 8 at 30 and 45 min, after a 20 s "Finisher next" gap. **None at 10 min**: with it, a 10-minute workout dropped to 1 round, which kills the progression. One high-output move from `FIN_POOL[focus]`, never one already used in the circuits; one-sided moves alternate sides each round. The finisher phase is deep red `#b91c1c`.
- **"How hard was that?":** shown after a completed workout. The answer is saved on the history entry. Too easy moves one setting one step harder for next time, in this order: difficulty, then work/rest preset, then shorter round rests. Too hard goes the other way, in reverse order. About right changes nothing. The screen says what changed and offers Undo.
- **One-sided moves:** each side gets a **full** work interval: left, a normal rest, then right. A one-sided move takes 2 slots in a circuit.
- **Audio:** beeps **and** voice. 3-2-1 beeps before the end of every interval, a double beep at 10 s left in work intervals of 25 s or more, a "go" tone when work starts, and a lower tone when work ends. During rests the voice says "Rest. Next, X, left side". At round rests it says "Round N done… Last round…" and at circuit changes "Circuit A done…". When the next round uses harder moves it adds "The moves step up". The voice uses the browser's speech synthesis in en-GB.
- **Experience level:** comfortable with the basics, so snatches, get-ups and windmills are included.
- **History:** saved on the phone in `localStorage`. Moves from the **last 2 sessions** are weighted down (×0.12) for variety.
- **Moves shown as:** looping stick-figure animations plus 2–3 form cues. The user accepted that the figures show the *shape* of a move, not fine technique.
- **Look:** dark, high-contrast and full screen while training. The background colour shows the phase: work is burnt orange `#c2410c`, rest is teal `#0f766e`, warm-up and cool-down are indigo `#4338ca`, get ready is amber `#a16207`.
- **Screen:** kept awake with the Wake Lock API, which is requested again when the page becomes visible.

## How `index.html` is organised (top to bottom)

1. **Storage:** `store.get/set` wraps `localStorage` with the prefix `kb_` and try/catch. The keys are `kb_settings` and `kb_history`, the latter a list of entries capped at 200.
2. **Figure engine:** draws a 2D figure (tapered limbs, solid torso, hands, feet, and a kettlebell with a handle) in an SVG with viewBox `0 0 200 190` and the ground at `GROUND=182`.
   - **Angles:** pose angles are **absolute, in degrees**. 0 points down, 90 points forward (right, the way the figure faces), 180 points up, and −90 points back. The direction vector is `D(a,len)=(sin a, cos a)·len`.
   - **Pose keys:** `t` torso (hip→shoulder), `hd` head offset, `na/nf` near upper arm and forearm, `fa/ff` far arm, `nt/ns` near thigh and shin, `ft/fs` far leg, `x` horizontal offset, `y` jump lift (negative is up), `b` where the bell is (`'n'` near hand, `'f'` far hand, `'both'`, `'hip'`, `'none'`), and `toe:1` to flip the feet (used when lying on the back).
   - **Extra pose keys (default 1):** `ls` scales the legs and `ts` the torso, to fake foreshortening (a torso tipped towards you, knees pointing at you). `sw` narrows the shoulders in front view to show the torso turning. `bo` is the bell's opacity; below 0.6 the bell is also drawn behind the body, for a bell passing behind the head or back.
   - **Grounding:** `fk()` works out the joint positions and then shifts the figure so its lowest point (feet, hands, knees, hip, head or bell) sits on the ground. That's why poses never specify a height.
   - **Front view:** a move with `view:'front'` draws front-on, with the shoulders and hips spread apart.
   - **Animation:** `kf:[[pose, seconds, easing?], …]` loops through the poses. Easing is `cos` (default), `snap` (fast start), `drop` (fast finish) or `lin`. Poses tagged `hike:1` (`HIKE1`, `HIKE2`) automatically snap up out of the hike and drop back into it, which gives swings, cleans and snatches their real rhythm. A duration of 0 jumps straight to the next pose, which the arm circles use to wrap from 360° back to 0°.
   - **Interpolation:** angles are interpolated as plain numbers, so pick values that don't swing the long way round. For example, use 230 rather than −130 when coming from 180, and −180 rather than 180 when coming from −90.
   - **Centring:** `m.cx` comes from `bounds()` and keeps each move centred.
   - **Bell trail:** the player and move sheet pass `{trail:1}`, which draws a faint dotted line along the bell's path for one loop. It's skipped when the bell barely moves.
   - **Arm helpers:** `ik2()` solves a two-link arm, `handsF()` places both hands in front view, `bellF()` places the bell itself in front view, and `unwrapKF()` keeps angles from swinging the long way round between keyframes. The halo, Russian twist, around the world, figure 8 and knees to chest are built with them.
3. **Poses and the move library:** `MOVES` holds 75 moves. Each has `{id, name, areas[], pat, uni, lvl, bw, cues[3], kf, view, thumb}`, plus `up` and `calls` where they apply.
   - **Ladders:** `UPS` maps a move ID to its harder version, which becomes `m.up`. Both ends must have the same `uni` setting, so a ladder never changes the number of slots.
   - **Complexes:** IDs start with `x_`. `calls:[[keyframe index, word], …]` lists the steps; the first must be at keyframe 0. The word is spoken and highlighted when the figure reaches that keyframe.
   - **areas:** any of `full`, `legs`, `upper`, `core`.
   - **pat:** one of `ballistic`, `squat`, `lunge`, `hinge`, `push`, `pull`, `arms`, `flex`, `antiext`, `rot`, `carry`.
   - Warm-ups are in `WARM` and stretches in `COOL`. Which ones each focus uses is set by `WARM_BY` and `COOL_BY`.
4. **Workout generator:**
   - **Finisher:** `FIN_W`, `FIN_R`, `FIN_SET`, `FIN_N[mins]` and `finSecs(mins)`. `buildWorkout` subtracts `finSecs` from circuit time before `fitPlan`, so the exact-length guarantee still holds. `wk.fin = {id, n}` or `null`; `sequence` adds `finset`, `fin` and `finrest` intervals before the cool-down.
   - **Base times:** `BASE[mins]=[warm-up seconds, cool-down seconds]`, plus `READY=10` and `SET=15` (the get-set gap between the warm-up and the circuits).
   - **`fitPlan(M,W,R,RR,maxSlots,allow)`:** searches circuits `c` (1–5), rounds `r` (1–4) and total slots `S`. The circuit time is `D = r·(S·W + (S−c)·R) + (r·c−1)·RR`. The score is `|M−D|·0.5` plus penalties: r≠3, an average of fewer than 4 or more than 6 slots per circuit, and each extra circuit.
   - **Exact length:** whatever is left over (`M−D`) is split between the warm-up and cool-down, then `spread()` divides each across its items. That's what makes the total exact.
   - **`chooseCircuits`:** fills the slots by working through `TEMPLATE[focus]`, the list of movement patterns for that focus. A one-sided move fits only where 2 slots are left. Each circuit is `{moves, ladders, rounds}`: `moves[i]` is the round-1 move and `ladders[i]` lists the move for every round.
   - **`ladderFor(m,rounds,diff,used)`:** builds one slot's ladder by following `up`, skipping any move already used elsewhere in the workout. No move appears in two slots.
   - **`swapMove`:** swaps a move for another of the same pattern with the same one-sided setting, then rebuilds that slot's ladder, so the timing doesn't change.
   - **`sequence(wk)`:** builds the list of intervals. Each has a kind (`ready|warm|set|work|rest|round|cool`), a duration, a move ID, a side, a circuit, a round and a pointer to what's next.
5. **Audio:** `initAudio()` must run from a user tap, which is why it's called from Start and Pause/Resume. `beep(freq,dur,vol)` uses Web Audio and `say(text)` uses speech synthesis.
6. **Setup UI, preview, move sheet, moves library and history.**
7. **Player:**
   - **Timer:** a 100 ms `setInterval` that advances by the real time elapsed, multiplied by `SPEED`. `SPEED` exists only so tests can fast-forward.
   - **Intervals:** `enter(i)` sets up an interval and `announce(it)` handles its sounds. Beeps fire when the count crosses a whole second.
   - **Complex steps:** during work the figure runs off `workClock()` (workout time, not wall time), so it pauses with the timer. `stepCall()` highlights the current step and, in move-by-move mode, speaks it. Calls stop in the last 3 seconds.
   - **Finishing:** `finish(complete)` saves the history entry, but only for sessions longer than 60 s. `setupRating()` wires the rating buttons; `nudge(dir)` works out the next setting change.
8. **Test hook:** `window.KB = {MOVES, WARM, COOL, ALL, buildWorkout, sequence, fitPlan, fk, setSpeed, PL, poseAt, makeFig, swapMove, stepAt, settings, nudge}`. Keep it, because the tests depend on it.

## Deploying

- **Method:** the Netlify site is linked to this repo. Every push to `main` deploys automatically, with no build command and the repo root as the publish folder. Work on other branches doesn't go live until it's merged into `main`.
- **Netlify free plan and private repos:** while the repo is private, Netlify only builds commits whose author is the one Git account linked to Netlify. Commits authored by anyone else, including `Claude <noreply@anthropic.com>`, fail with "Build failed: unrecognized Git contributor", and the push looks as if it did nothing. The repo was made public on 2026-11-14 to fix this. If it goes private again, author commits as the linked account, or upgrade the Netlify plan. After a failed build, use **Retry → Deploy with latest branch commit** in the Netlify UI.
- **After changing cached files, bump the cache name** in `sw.js` (`kb-v1` → `kb-v2`) so old copies are cleared. The worker fetches from the network first, so normal updates appear on the next online visit anyway.
- **Powered by Netlify badge:** turned off in the Netlify UI under Project configuration → General.
- **Service worker:** registers only over `https:` (see the end of `index.html`), so local `file://` testing skips it.

## Testing

You need Python 3 with Playwright (`pip install playwright && playwright install chromium`). If Playwright's own browser is missing or the wrong version, run the scripts with `USE_SYSTEM_CHROME=1` to use the installed Chrome or Chromium instead.

```bash
python3 tests/check_timing.py   # every length × focus × interval × round-rest × difficulty × finisher combination: exact length before and after swaps, finisher present and not repeating a circuit move, no repeated moves, ladders keep the one-sided setting
python3 tests/render_moves.py   # draws every move's keyframes to tests/out/moves.png so you can look at them
python3 tests/run_through.py    # phone-sized run: setup → preview → swap → play at 60–400× speed → summary → history → moves, checks the finisher ran and the rating buttons (change, Undo, saved rating), then a Brutal workout to check complex steps in both voice modes; fails on JS errors
```

Look at `moves.png` after any change to poses. A bad angle usually shows up as a figure floating, sinking, or upside down.

## Known limitations and ideas

- **Figures:** still schematic. The halo, Russian twist, around the world and figure 8 now use front views, which read better than the old side views, but the hands sometimes cross the face in the halo. Knees to chest is still the weakest figure.
- **10 kg is light for legs:** the library leans on single-leg, tempo and pulse moves to make up for it. A heavier bell would need either a weight setting or no changes at all, since timings don't depend on load.
- **History:** stays on one device and is lost if Chrome's site data is cleared. There's no export yet.
- **Voice:** depends on the phone's text-to-speech engine.
- **Complex voice on the phone:** move-by-move calls were only tested in desktop Chrome with speech stubbed. Android text-to-speech can lag or drop short words; check on the real phone.
- **Suggested to the user, not built yet:** highlighting the working muscles on the figure.
- **Rating levers:** the rating never touches length, focus or a custom work/rest setting. At the top of every lever it suggests a heavier bell.
- **Ideas the user hasn't asked for yet:**
  - history export/import (JSON)
  - progression tracking
  - a "favourite/never show" toggle per move
  - workout presets
  - a halfway voice cue
  - better figure art

## Security

Reviewed on 2026-11-14. The app is a static page in Chrome's sandbox: it opens no ports, runs no server on the phone and asks for no permissions beyond keeping the screen awake. It takes no text input and reads nothing from the URL.

- **Headers:** `netlify.toml` sends a Content-Security-Policy that only allows the site's own files; the app makes no requests to any other site. If you add any outside resource (a CDN script, an image host, an API), add its host to the CSP or the browser will block it. `'unsafe-inline'` is needed because the script and styles live in `index.html`.
- **Stored data is untrusted:** history comes from `localStorage` through `hist()`, which drops malformed entries, and every field is passed through `esc()` before it goes into HTML. Keep doing both for anything new read from storage.
- **Who controls the code:** only the `Dresdenjass84` GitHub account can push. Whoever can push to `main`, or log in to Netlify, controls what runs on the phone, so both accounts should have two-factor authentication.
- **Fonts:** self-hosted in `fonts/` since 2026-11-14, so Google no longer sees the phone's IP address. Only the Latin subset is included; accented letters outside it fall back to the system font. Font files are cached for a year, so give a changed font a new file name.

## Working rules for this repo

- Keep it **one static file plus the PWA files**, with no build step, unless the user agrees otherwise.
- Use British English in the interface text.
- Run all three test scripts before committing changes to timing, the generator or poses.
- Never weaken the exact-length guarantee.

## Changelog

- **2026-11-08:** first release, deployed to Netlify. Installable on Android and works offline.
- **2026-11-13:** handover to this repo. Fixed two generator bugs found by the new tests:
  - A 10-minute workout with 120 s work and 90 s rest crashed, because no plan fitted. `fitPlan` now falls back to smaller circuits.
  - A 45-minute legs workout at 15/5 came out 60 s short, because the move pool ran out of moves. `buildWorkout` now times the circuits it actually filled.
- **2026-11-14:** Netlify linked to this repo, so pushes to `main` now deploy automatically. The two generator fixes above went live with the first linked deploy.
- **2026-11-14:** difficulty setting with progressive rounds, 11 harder moves and 10 complexes, and a switch for how the voice handles complexes. Service worker cache bumped to `kb-v2`.
- **2026-11-14:** fuller figures (tapered limbs, torso, hands, feet, kettlebell with handle), a dotted bell trail, snap-and-drop rhythm for ballistic moves, and front views for the halo, Russian twist, around the world and figure 8. Cache bumped to `kb-v3`.
- **2026-11-14:** finisher (20/10 all-out before the cool-down, none at 10 min) and a "How hard was that?" rating that nudges one setting for next time, with Undo. Fixed "1 rounds" in the preview. Cache bumped to `kb-v4`.
- **2026-11-14:** security review. Added security headers in `netlify.toml`, escaped stored history before display, and made the app ignore malformed history entries. Cache bumped to `kb-v5`.
- **2026-11-14:** fonts self-hosted instead of loaded from Google Fonts, CSP tightened to the site's own files only, fonts precached for offline use. Cache bumped to `kb-v6`.
