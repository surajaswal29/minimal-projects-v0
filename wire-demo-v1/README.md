# Wire demo v1: HTML + CSS talking to a server

An experiment in making pages live and server-driven **without any JavaScript in the browser**. The page is only HTML and CSS. The only code is `server.py`, which runs on the server and uses nothing but the Python standard library.

Open the page in two windows and they update each other.

## Run it

```bash
cd wire-demo-v1
python3 server.py            # http://127.0.0.1:8000/
PORT=9000 python3 server.py  # choose another port
```

It needs the server. If you open `index.html` straight from disk, you only see the layout.

## The five techniques

| # | Technique | HTML/CSS used | Server route |
|---|---|---|---|
| 1 | **Form → named iframe**: update one region | `<form target="likes">` + `<iframe name="likes">` | `POST /like` → 303 → `GET /frag/likes` |
| 2 | **Self-rendering form**: the form clears itself after sending | A form inside an iframe that posts to itself | `POST /frag/comment-form` |
| 3 | **Streaming "forever frame"**: server push | `<iframe src="/stream/comments">`. The response never ends. | `GET /stream/comments` |
| 4 | **Polling fragment**: refreshes on a timer | `<meta http-equiv="refresh" content="3">` inside the frame | `GET /frag/stats` |
| 5 | **CSS beacons**: send events from CSS | `.choice:has(:checked) { background-image: url("/beacon?e=…") }` | `GET /beacon` → 204 |

**Bonus: out-of-order streaming.** The page layout is a Declarative Shadow DOM (`<template shadowrootmode>`) with named `<slot>`s. The server streams the page, waits 1.5 s, then sends the "Server report" section last. It still appears near the top, in its slot. Until it arrives, the slot shows its fallback content.

## Files

```text
wire-demo-v1/
├── index.html   # page layout (the server splits it at <!--WIRE:SLOW-->)
├── styles.css   # styles for the page and every fragment
├── server.py    # the Wire server (standard library only)
└── README.md
```

## Limitations (honest ones)

- **The loading spinner never stops.** Because the message stream never finishes, the page's `load` event never fires. That's the classic downside of forever frames.
- **Iframes have fixed heights.** They don't size themselves to their content without JS, so each frame's height is set in CSS.
- **Each CSS beacon fires once per page load.** The browser caches the image request, so re-checking the same option doesn't send it again.
- **Every live tab keeps one HTTP connection open.** Browsers allow about 6 connections per host over HTTP/1.1, so many tabs open at once can stall. Serving over HTTP/2 through a reverse proxy removes that limit.
- State is kept in memory and resets when the server restarts. Messages are escaped and length-limited, and only a fixed set of beacon events is counted.

## Browser support

Current Chrome, Edge, Safari and Firefox. `:has()` and Declarative Shadow DOM (`shadowrootmode`) are required.
