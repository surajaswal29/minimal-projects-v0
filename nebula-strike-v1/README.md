# Nebula Strike — a 3D arcade shooter in HTML + CSS

A 60-second synthwave shooting gallery. Drones, gold cores and mines fly at you out of a 3D nebula. Click them to shoot. The game uses **HTML and one CSS file**, with **zero JavaScript**.

| Target | Points |
|---|---|
| Drone (spinning neon cube) | +1 |
| Gold core (cube with orbiting rings) | +5 |
| Mine (red wireframe sphere) | −3 |

## Structure

```text
nebula-strike-v1/
├── index.html   # The whole game: one <form>
├── styles.css   # Scene, targets, HUD and panels, in cascade layers
└── README.md
```

## How it works without JavaScript

| Game mechanic | Technique |
|---|---|
| Game state | Start, pause and difficulty are checkboxes and radios, read anywhere with `.game:has(#start:checked)`. |
| 3D world | `perspective` on `.world`, `transform-style: preserve-3d` down to each cube's six faces. Targets animate separate `translate` (flight from `z: -3200px` toward the camera) and `scale` (pop in/out) properties, so the two never fight. |
| Shooting | Each target is a `<label>` for a visually hidden checkbox. `.hit:checked + .target` pauses its flight (`animation-play-state: paused`), shrinks the body and plays the explosion: a shockwave ring, a flash, 8 shards and a floating "+1". |
| Score | CSS counters: `.hit.cube:checked { counter-increment: score 1 drones 1 }`, mines count `-3`. The HUD comes after the targets in the document, so `content: counter(score)` prints the running total. |
| Timer | A typed `@property --t` (`<integer>`) animated from 60 to 0 and printed with `counter-reset: t var(--t)`. The progress bar is a `scale` animation over the same 60 s. |
| Last 10 seconds | A red vignette and a flashing timer, using animations with a 50 s delay. |
| Game over | An overlay with `animation-delay: 60s`. It reads the same counters for the final score and tally. |
| Pause | Setting `animation-play-state: paused` on everything freezes the whole game, including the timer and the game-over delay. |
| Restart | A native `<button type="reset">` unchecks every target and the start box, so the next launch restarts every animation. The difficulty radios use `form="prefs"` (an empty second form), so a reset keeps the chosen difficulty. |
| Logo | A **declarative shadow DOM** component: `<neon-logo><template shadowrootmode="open">` holds encapsulated styles for the 3D sway and glint. The slotted `<h1>` still uses the page stylesheet. |
| Explainer | A `popover` opened with `popovertarget`, with an `@starting-style` entry transition. |
| Backdrop | Warp starfield (3 scaling gradient layers), a rotating blurred nebula, a striped sun (`mask` with an animated stripe layer), `clip-path` mountains and a `rotateX(74deg)` scrolling grid floor. |

### Why no `<canvas>`?
`<canvas>` has no drawing API outside JavaScript. On its own it is an empty box. So the 3D here comes from CSS transforms, and `<template>` is used the one way that works without scripts: declarative shadow DOM.

## Accessibility and preferences

- Every target is a real checkbox with an `aria-label`. You can Tab to targets and press Space to shoot them; the focused target gets an outline.
- Access keys: `S` launches and `P` pauses (the modifier depends on the browser, e.g. Alt+Shift on Chrome/Windows).
- `prefers-reduced-motion: reduce` turns off decorative motion (stars, nebula, grid, spin, glint) and slows every difficulty down. Only the flight paths and the timer keep moving.
- The game is always dark (`color-scheme: dark`) by design.

## Browser support

This needs a current evergreen browser. It relies on `:has()`, `@property`, individual transform properties, `color-mix()` and declarative shadow DOM (Chrome/Edge 111+, Safari 16.4+, Firefox 128+). If declarative shadow DOM is missing, the logo still renders, just without the sway.

## Limitations

- Missed targets can't be counted, since there is no event for "a target flew past". The score only counts hits.
- There is no high score, because nothing can be saved without JS or a server.
- The target paths are fixed in the HTML (generated once with a seeded random script), so each round follows the same pattern.

## Run it

Open `index.html` in a browser. No server or build step is needed.

Total weight: about 23 KB of HTML and 27 KB of CSS, in 2 requests.
