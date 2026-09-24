# Product Portfolio v1: Stillwater

A single-page portfolio for a fictional product studio called **Stillwater**. It is minimal and modern, with a soft sage-and-sand palette. It is built with **HTML and CSS only**: no JavaScript, no frameworks and no external fonts.

## Files

```text
product-portfolio-v1/
├── index.html   # the page
├── styles.css   # every style for the page
└── README.md
```

## Sections

Hero with stats → client names → product portfolio with filters → principles → process → testimonial → FAQ → contact form → footer.

## How the interactions work without JavaScript

| Feature | Technique |
|---|---|
| Mobile menu | The `popover` attribute and `popovertarget`. Older browsers show the nav inline. |
| Product filters | Radio buttons and `:has()` hide the cards that don't match |
| FAQ accordion | `<details>` / `<summary>` with `name="faq"`, so only one answer is open at a time |
| Form validation | Native `required`, `type="email"`, `minlength` and `:user-invalid` styling |
| Form submission | `mailto:`. To use a real backend, change the form's `action` to a form service. |
| Product artwork | Drawn entirely with CSS gradients and shapes, with no images |

## Design notes

- The CSS is organized into cascade layers (`reset, tokens, base, layout, components, pages, utilities`).
- Colors come from design tokens built with `light-dark()`, so dark mode follows the system setting.
- Type and spacing scale fluidly with `clamp()`. Headings use a system serif and body text uses a system sans-serif.
- Motion is turned off when the visitor has `prefers-reduced-motion: reduce` set.

## Run it

Open `index.html` in a browser, or serve the repository root:

```bash
python3 -m http.server 8000
# http://localhost:8000/product-portfolio-v1/
```

## Browser support

Current versions of Chrome, Edge, Safari and Firefox. `:has()`, `popover` and `light-dark()` are required for the full experience. In older browsers the menu still works because it falls back to an inline nav.
