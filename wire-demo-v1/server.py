"""Wire demo server.

The browser side of this demo is pure HTML + CSS. This file is the only code,
and it runs on the server. It shows five ways a page can talk to a server
without JavaScript:

  1. Form -> named iframe      POST /like, the result lands in <iframe name="likes">
  2. Self-contained fragment   GET/POST /frag/comment-form, a form that re-renders itself
  3. Streaming "forever frame" GET /stream/comments, which stays open and pushes new HTML
  4. Polling fragment          GET /frag/stats, which refreshes itself with <meta refresh>
  5. CSS beacons               GET /beacon?e=..., requested by CSS background-image rules

The main page is also streamed out of order. The shell is sent right away, and
a slow "server report" is sent last but shows up in the middle of the layout,
via Declarative Shadow DOM slots.

Standard library only. Run:  python3 server.py   (PORT env var, default 8000)
"""

import html
import os
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = {"/styles.css": ("styles.css", "text/css; charset=utf-8")}
SLOW_MARKER = "<!--WIRE:SLOW-->"
BEACON_EVENTS = {"vote-forms", "vote-streams", "vote-polling", "vote-beacons", "how-open"}

# ---------------------------------------------------------------------------
# In-memory state (resets when the server restarts)
# ---------------------------------------------------------------------------
lock = threading.Lock()
new_comment = threading.Condition(lock)
state = {
    "started": time.time(),
    "likes": 0,
    "comment_seq": 0,
    "streams": 0,
    "beacons": {e: 0 for e in BEACON_EVENTS},
}
comments = deque(maxlen=50)  # (id, name, text, timestamp)


def add_comment(name, text):
    with new_comment:
        state["comment_seq"] += 1
        comments.append((state["comment_seq"], name, text, time.time()))
        new_comment.notify_all()


add_comment("Wire", "Welcome! Post a message and watch it appear here with no reload and no JavaScript.")


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------
def fragment_page(body, body_class="", refresh=None):
    meta = f'<meta http-equiv="refresh" content="{refresh}">' if refresh else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="color-scheme" content="light dark">'
        f'{meta}<link rel="stylesheet" href="/styles.css"></head>'
        f'<body class="frag {body_class}">{body}</body></html>'
    )


def comment_html(c):
    _, name, text, ts = c
    when = time.strftime("%H:%M:%S", time.localtime(ts))
    return (
        f'<article class="msg"><header><strong>{html.escape(name)}</strong>'
        f'<time>{when}</time></header><p>{html.escape(text)}</p></article>\n'
    )


def report_html():
    with lock:
        up = int(time.time() - state["started"])
        data = dict(likes=state["likes"], comments=state["comment_seq"], streams=state["streams"])
    return (
        '<section slot="report" class="card report">'
        '<p class="label">Streamed last · shown here</p>'
        '<h2>Server report</h2>'
        f'<p>This card was sent <strong>after</strong> the rest of the page, about 1.5 s late, '
        f'yet it sits near the top. The server filled a slot in a Declarative Shadow DOM layout.</p>'
        f'<dl class="kv"><div><dt>Uptime</dt><dd>{up // 60}m {up % 60}s</dd></div>'
        f'<div><dt>Likes</dt><dd>{data["likes"]}</dd></div>'
        f'<div><dt>Messages</dt><dd>{data["comments"]}</dd></div>'
        f'<div><dt>Live streams</dt><dd>{data["streams"]}</dd></div></dl>'
        '</section>\n'
    )


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "Wire/0.1"

    # -- plumbing ------------------------------------------------------------
    def send_html(self, body, status=200):
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def start_stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")  # ask proxies not to buffer
        self.send_header("Connection", "close")
        self.end_headers()

    def write(self, text):
        self.wfile.write(text.encode())
        self.wfile.flush()

    def form_data(self):
        length = min(int(self.headers.get("Content-Length") or 0), 10_000)
        raw = self.rfile.read(length).decode("utf-8", "replace")
        return {k: v[0] for k, v in parse_qs(raw).items()}

    def log_message(self, fmt, *args):
        if "/frag/stats" not in (args[0] if args else ""):
            super().log_message(fmt, *args)

    # -- routes --------------------------------------------------------------
    def do_GET(self):
        url = urlparse(self.path)
        route = {
            "/": self.page,
            "/index.html": self.page,
            "/frag/likes": self.frag_likes,
            "/frag/stats": self.frag_stats,
            "/frag/comment-form": self.frag_comment_form,
            "/stream/comments": self.stream_comments,
            "/beacon": self.beacon,
        }.get(url.path)
        if route:
            return route(parse_qs(url.query))
        if url.path in STATIC:
            name, ctype = STATIC[url.path]
            with open(os.path.join(ROOT, name), "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        self.send_html(fragment_page("<p>Not found.</p>"), 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/like":
            with lock:
                state["likes"] += 1
            return self.redirect("/frag/likes")
        if path == "/frag/comment-form":
            data = self.form_data()
            name = data.get("name", "").strip()[:40]
            text = data.get("message", "").strip()[:280]
            if not name or not text:
                return self.redirect("/frag/comment-form?error=1")
            add_comment(name, text)
            return self.redirect("/frag/comment-form?sent=1")
        self.send_html(fragment_page("<p>Not found.</p>"), 404)

    # 0. The main page, streamed out of order
    def page(self, _query):
        with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
            first, _, rest = f.read().partition(SLOW_MARKER)
        self.start_stream()
        try:
            self.write(first)
            time.sleep(1.5)  # pretend this part needs a slow database query
            self.write(report_html())
            self.write(rest)
        except (BrokenPipeError, ConnectionResetError):
            pass

    # 1. Target of the like form
    def frag_likes(self, _query):
        with lock:
            n = state["likes"]
        body = f'<p class="big">{n}</p><p class="muted">likes from everyone</p>'
        self.send_html(fragment_page(body, "center", refresh=5))

    # 2. Form that re-renders itself, so it clears after a successful send
    def frag_comment_form(self, query):
        note = ""
        if "sent" in query:
            note = '<p class="note ok" role="status">Sent. Look at the wall →</p>'
        elif "error" in query:
            note = '<p class="note err" role="alert">Please fill in both fields.</p>'
        body = (
            '<form method="post" class="stack">'
            '<label>Name <input name="name" required maxlength="40" autocomplete="nickname"></label>'
            '<label>Message <textarea name="message" required maxlength="280" rows="3"></textarea></label>'
            f'<button type="submit">Post message</button>{note}</form>'
        )
        self.send_html(fragment_page(body))

    # 3. Forever frame: the response never ends and new HTML is appended as it happens
    def stream_comments(self, _query):
        self.start_stream()
        with lock:
            state["streams"] += 1
        last = 0
        try:
            self.write(
                '<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="color-scheme" content="light dark">'
                '<link rel="stylesheet" href="/styles.css"></head><body class="frag wall">\n'
            )
            while True:
                with new_comment:
                    fresh = [c for c in comments if c[0] > last]
                    if not fresh:
                        new_comment.wait(timeout=15)
                        fresh = [c for c in comments if c[0] > last]
                if fresh:
                    last = fresh[-1][0]
                    self.write("".join(comment_html(c) for c in fresh))
                else:
                    self.write("<!-- keep-alive -->\n")  # also detects closed tabs
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with lock:
                state["streams"] -= 1

    # 4. Polled every 3 seconds via <meta http-equiv="refresh">
    def frag_stats(self, _query):
        with lock:
            s = dict(state, beacons=dict(state["beacons"]))
        b = s["beacons"]
        votes = [("Forms → iframe", b["vote-forms"]), ("Streaming", b["vote-streams"]),
                 ("Polling", b["vote-polling"]), ("CSS beacons", b["vote-beacons"])]
        total = max(sum(v for _, v in votes), 1)
        bars = "".join(
            f'<li><span>{label}</span><meter min="0" max="{total}" value="{v}">{v}</meter><b>{v}</b></li>'
            for label, v in votes
        )
        body = (
            f'<dl class="kv"><div><dt>Server time</dt><dd>{time.strftime("%H:%M:%S")}</dd></div>'
            f'<div><dt>Watching live</dt><dd>{s["streams"]}</dd></div>'
            f'<div><dt>Likes</dt><dd>{s["likes"]}</dd></div>'
            f'<div><dt>“How” opened</dt><dd>{b["how-open"]}</dd></div></dl>'
            f'<p class="label">Favourite technique (CSS beacon votes)</p><ul class="bars">{bars}</ul>'
        )
        self.send_html(fragment_page(body, refresh=3))

    # 5. Requested by CSS background-image rules. Responds with an empty 204.
    def beacon(self, query):
        event = query.get("e", [""])[0]
        if event in BEACON_EVENTS:
            with lock:
                state["beacons"][event] += 1
        self.send_response(204)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    print(f"Wire demo running at http://{host}:{port}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
