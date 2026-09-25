# Almanac — a slow guide to the seasons

A calm, single-page field guide: what to sow, what to notice and how the light changes through the year. Pick a season and the whole page re-themes, including the colours, the landscape, the text and the chart.

Built with **HTML and one CSS file only**: no JavaScript, no frameworks, no web fonts, no images.

## Structure

```text
seasonal-almanac-v1/
├── index.html   # the page
├── styles.css   # all styles, organised in cascade layers
└── README.md
```

## How it works without JavaScript

| Feature | Technique |
|---|---|
| Season dial | Four radio inputs in a `<fieldset>`. `:root:has(#s-autumn:checked)` swaps the season tokens (`--accent`, `--wash`, sky, sun, hills, specks). |
| Season content | Elements tagged `data-season="…"` are hidden unless their season is checked. |
| Landscape | Positioned `div`s and gradients. The sky colours are registered with `@property` so the gradient animates between seasons. Falling petals, pollen, leaves or snow use `cqw` units inside a size container. |
| Daylight chart | An ordered list of bars sized by a `--h` custom property. The chosen season's months are highlighted in the accent colour, and hovering a bar shows its value. |
| Moon phases | Circles drawn with inset `box-shadow` crescents and half-and-half gradients. |
| Field guide | A horizontal `scroll-snap` rail of plant cards with CSS-drawn illustrations. |
| Newsletter | Native `type="email"` + `required` validation and a `mailto:` action. Replace it with a form service endpoint for real use. |

## Accessibility and preferences

- Real radio inputs with a legend, so the dial works with the keyboard (arrow keys) and screen readers.
- Visible focus rings, a skip link and semantic landmarks.
- Light and dark mode via `light-dark()`, with a dusk version of each season's landscape.
- `prefers-reduced-motion: reduce` turns off the drifting clouds, falling specks and transitions.

## Browser support

This uses `:has()`, `light-dark()`, `@property`, container query units and `color-mix()`, which are all supported in current Chrome, Edge, Safari and Firefox. Browsers without `:has()` get the spring edition with the dial hidden.

## Run it

Open `index.html` in a browser, or serve the repo root with `python3 -m http.server`.
