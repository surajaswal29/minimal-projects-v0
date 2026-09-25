# Kiln — a small ceramics studio

A calm, **multipage** website for a fictional two-person pottery studio: a shop, classes, a journal with a long-form article, a studio/about page and a contact form.

Built with **HTML and one shared CSS file only**: no JavaScript, no frameworks, no web fonts, no images. Every pot is drawn in CSS.

## Structure

```text
ceramics-studio-v1/
├── index.html           # Home: hero, new pieces, classes teaser, journal, commissions
├── shop.html            # The collection, with CSS-only filters and an FAQ
├── classes.html         # Class cards, autumn schedule table, FAQ
├── journal.html         # Journal index
├── journal-glazes.html  # A long-form article
├── about.html           # Story, process, people, map and opening hours
├── contact.html         # Contact form and studio details
├── styles.css           # All styles, organised in cascade layers
└── README.md
```

## How it works without JavaScript

| Feature | Technique |
|---|---|
| Page transitions | Cross-document view transitions (`@view-transition { navigation: auto; }`). The header and page title have their own `view-transition-name`, so they morph between pages. |
| Current page | Each page marks its nav link with `aria-current="page"`, which is also the styling hook. |
| Mobile menu | The nav is a `popover` opened by a `popovertarget` button, with `@starting-style` entry animation. Above the breakpoint it's a normal inline nav. |
| Shop filters | Radio inputs + `:has()`: e.g. `.shop:has(#f-cups:checked) .card:not([data-cat~="cups"])` is hidden. "In stock" hides cards that contain a `.sold` tag. The item count swaps the same way. |
| CSS pots | `.art` is the stage and `.pot` the vessel. Shape modifiers (`cup`, `tumbler`, `bowl`, `vase`, `bottle`, `plate`) change the border radius; `--glaze` and `--clay` set the colours. |
| FAQs | Exclusive accordions via `<details name="faq">`, animated with `::details-content` and `interpolate-size`. |
| Contact form | Native validation with `:user-invalid` styling and a `mailto:` action. Replace it with a form service endpoint for real use. |

## Accessibility and preferences

- Semantic landmarks, a skip link, breadcrumbs and visible focus rings on every page.
- Filters are real radio inputs in a `<fieldset>`, so they work with the keyboard and screen readers.
- Light and dark mode via `light-dark()`.
- `prefers-reduced-motion: reduce` turns off view transitions, animations and transitions.

## Browser support

Uses `:has()`, `light-dark()`, `popover`, `color-mix()` and cascade layers, supported in current Chrome, Edge, Safari and Firefox. View transitions and animated `<details>` are progressive enhancements: browsers without them simply navigate and open instantly.

## Run it

Open `index.html` in a browser, or serve the repo root with `python3 -m http.server` (view transitions need an `http://` origin, not `file://`).
