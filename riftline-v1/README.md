# Riftline: a 3D pipe racer in HTML + CSS

A 90-second run down a neon half-pipe toward a glowing core. You steer across five lanes, jump fences, stay low under lasers and grab shards. Hazards really hit you: shields drain, the hull breaks apart, and the run ends. The game uses **HTML and CSS only, with zero JavaScript** in the browser.

CSS-only games are usually click-the-target or `:hover` maze games. Riftline adds **collision detection between a player you steer and moving 3D obstacles**, plus damage that builds up over the run. Each is decided per frame by the style engine.

| Thing | What to do | Score |
|---|---|---|
| Wall (pink crystal) | Change lanes | Hit: −1 shield |
| Fence (amber stripes) | Jump | Hit: −1 shield |
| Laser gate (red beam) | Stay low, do not jump | Hit: −1 shield |
| Gold shard | Stay low in its lane | +100 |
| Violet shard (with a light pillar) | Jump in its lane | +100 |
| Distance | Survive | +1 per metre (9000 m to the core) |

You have 3 shields. A full hit costs one; a graze costs a fraction of one. The run has three sectors (Neon Veins, Solar Rift, Event Horizon), and each one is faster and denser than the last.

## Controls

| Input | Action |
|---|---|
| `←` `→` (or `↑` `↓`) | Steer. At the edges the radio group wraps around, which is a quick way across. |
| Hold `Space` | Jump |
| Mouse / touch | Click or tap left or right of the ship to steer, hold the middle to jump |
| Pause / Restart | HUD buttons, or the access keys `P` and `R` (for example Alt+Shift+P in Chrome on Windows) |

If focus leaves the lanes (after pausing, say), a hint asks you to click the track or press Tab.

## Structure

```text
riftline-v1/
├── index.html      # The game: one <form>. The course markup is generated.
├── styles.css      # Scene, pipe, ship, obstacles, HUD, panels (hand-written)
├── course.css      # Collision timeline and rules (generated)
├── tools/course.py # Build-time course generator (Python, never sent to the browser)
└── README.md
```

To change the course, edit `tools/course.py` (seed, speeds, patterns) and run `python3 tools/course.py`. It rewrites `course.css` and the marked regions of `index.html`. It also checks that no two hazards overlap in one lane, and that every row leaves a lane the player can reach.

## How it works without JavaScript

CSS can only pass values **down** the tree, so the game state is stacked from the root:

```text
<html>     course clock: --l0…--l4 (what is in each lane right now), --sector
  <body>   hull: a paused "drain" animation → --shield 3→0, --dead 0→1
    .game  mission clock → --won; the lane radios live in here
      .o   each obstacle / shard: its flight plus its own --hot hit window
        .x a 50 ms latch → --boom and a counter-increment
```

| Mechanic | Technique |
|---|---|
| Steering | Five visually hidden **radio buttons** are the lanes. Arrow keys move between radios natively. `.game:has(#l3:checked)` sets `--a: -30deg`, and the ship rig rotates to that angle around the pipe's axis. |
| Jumping | Holding Space on the focused radio makes it `:active`. The selector is `.lane:focus-visible:active`, because a mouse click on a label also makes its radio `:active` but not `:focus-visible`, so steering by mouse never counts as a jump. Mouse and touch use `.pad-jump:active`. |
| Course timeline | `course.css` has one `steps(1, end)` animation per lane on `<html>`. Each sets a typed `@property` integer (`0` clear, `1` wall, `2` fence, `3` laser) for the 0.18 s a hazard overlaps the ship. |
| **Collision** | A **container style query** on `<html>`: `@container style(--l3: 1) { body:has(#l3:checked) { animation-play-state: running } }`. It matches only while you are in lane 3 and a wall is there. Fences add `:not(:has(<jumping>))` and lasers add `:has(<jumping>)`. |
| **Damage that sticks** | The rule above un-pauses the `drain` animation on `<body>`. A paused animation keeps its progress, so damage **accumulates** and never resets. 0.54 s of contact drains `--shield` from 3 to 0, and the last keyframe flips `--dead` to 1. |
| Game over | Everything below `<body>` inherits `--dead`. `@container style(--dead: 1)` freezes the world (the last cascade layer pauses every track animation), flies the hull parts apart, shows the explosion and brings up the score card. |
| Per-object hits | Each object animates its own `--hot` window. Its child `.x` runs a 50 ms "latch" animation only while its parent is hot **and** you are in its lane at the right height. `fill-mode: forwards` keeps the end state: `--boom: 1` (the shard bursts, the wall shatters) and a `counter-increment`. |
| Score | `.tally` resets the counters: `counter-reset: score var(--dist)`, where `--dist` is an animated integer odometer. Each collected shard's latch adds `counter-increment: score 100 shards 1`. The HUD comes later in the document, so `content: counter(score)` prints distance + 100 × shards. |
| Sectors | A stepped `--sector` on `<html>`. `@container style(--sector: 2)` swaps registered `<color>` properties, and a transition on those properties re-themes the whole scene. Rings speed up and a warp flash covers the change. |
| Banking | Two nested rotations: one follows the lane angle instantly (−1.4 × a), the other with a slow transition (+1.4 × a). Their sum is a roll into each turn that settles back to level, with no knowledge of the previous lane. |
| Victory | `.game` runs a 90 s clock that flips `--won` at the end. It pauses when `--dead` is 1, so only a surviving pilot reaches the core. |
| Restart | `<button type="reset">` clears the radios. The `:has(.lane:checked)` rules stop matching, so every clock is removed and starts over on the next launch. |
| 3D | `perspective` on `.view` and `preserve-3d` through the camera, pipe, obstacles and ship. The ship is built from `clip-path` polygons. Obstacles move with the individual `translate` property, so their placement `transform` never fights the flight. Opacity is kept off 3D groups, since opacity would flatten them. The explosion is drawn in 2D at the ship's projected position, so no 3D plane can slice it. |

### Why the course is fixed
With no scripting there is no randomness at runtime, so the course is generated once from a seed. It follows a hand-tuned difficulty curve: a tutorial for each hazard, then patterns such as gates, slaloms, fence lines and laser rows, with rewards placed over and under them.

## Accessibility and preferences

- The lanes are a real, labelled radio group, and the pause control is a real checkbox, so everything works from the keyboard.
- `prefers-reduced-motion: reduce` removes camera shake, lean, banking, the warp stars and other decoration. Gameplay is unchanged.
- The page is always dark (`color-scheme: dark`) by design.

## Browser support and limitations

- Needs a current evergreen browser with **container style queries for custom properties** (Chrome/Edge 111+ and Safari 18+; check Firefox's current support before relying on it). It also uses `@property`, `:has()`, individual transform properties and `color-mix()`.
- Collision is checked once per rendered frame. At normal frame rates a 0.18 s hit window spans about 10 frames. A device that stalls for more than 0.18 s at once can miss a hit.
- Hold-to-jump on touch needs the browser to apply `:active` while a finger is held down. iOS Safari only does that for elements with touch event listeners, which a page with no JavaScript cannot add, so on iPhone use a keyboard or accept that you cannot jump.
- There are no high scores, because nothing can be saved without JavaScript or a server.

## Run it

Open `index.html` in a browser. No server or build step is needed.
