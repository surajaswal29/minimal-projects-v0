#!/usr/bin/env python3
"""Build the Riftline course.

This is a build-time tool only. The browser never runs it. It lays out a
seeded, always-solvable 90-second course and writes two things:

  * course.css : the collision timeline on <html> (one stepped animation per
                 lane), the sector clock, the flight keyframes for each speed
                 tier and the collision / pickup rules.
  * index.html : the markup for every obstacle, shard and tutorial hint,
                 between the "course:begin" / "course:end" and
                 "hints:begin" / "hints:end" markers.

Run it from anywhere:  python3 riftline-v1/tools/course.py
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 1947

LANES = 5
RUN = 90.0            # seconds to reach the core (victory)
SCHEDULE = 92.0       # length of the collision timeline on <html>
SECTOR_AT = (30.0, 60.0)
LAST_HAZARD = 87.2    # nothing to hit during the final approach

ZFAR, ZPAST = 900, 50  # flight path in u: spawn depth and how far past the ship it goes
HALF = 0.09            # half of a hit window, in seconds (a full hit lasts 0.18 s)

# Seconds from spawn until an object reaches the ship, per sector.
TIERS = {1: 2.4, 2: 1.95, 3: 1.6}
# Random gap between rows (seconds), per sector.
GAPS = {1: (0.95, 1.3), 2: (0.78, 1.05), 3: (0.62, 0.86)}

HAZARD_CODE = {"wall": 1, "fence": 2, "beam": 3}
JUMP = ".lane:focus-visible:active, .pad-jump:active"


@dataclass
class Obj:
    kind: str   # wall | fence | beam | gem | sky
    lane: int
    hit: float  # time the object reaches the ship

    @property
    def tier(self) -> int:
        return tier_at(self.hit)

    @property
    def spawn(self) -> float:
        return self.hit - TIERS[self.tier]


def tier_at(t: float) -> int:
    if t < SECTOR_AT[0]:
        return 1
    if t < SECTOR_AT[1]:
        return 2
    return 3


def flight(tier: int) -> float:
    return TIERS[tier] * (ZFAR + ZPAST) / ZFAR


# --------------------------------------------------------------------------
# Course layout
# --------------------------------------------------------------------------

class Course:
    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.objs: list[Obj] = []
        self.hints: list[tuple[float, str, str]] = []
        self.safe = set(range(LANES))  # passable lanes of the previous row

    # A row is {lane: kind}. Rows must leave a passable lane that the player
    # can reach from the previous row's passable lanes.
    def reachable(self, row: dict[int, str], reach: int) -> bool:
        passable = {k for k in range(LANES) if row.get(k) != "wall"}
        if not passable:
            return False
        return any(abs(a - b) <= reach for a in passable for b in self.safe)

    def put(self, t: float, row: dict[int, str], extra: list[Obj] | None = None) -> None:
        for lane, kind in row.items():
            self.objs.append(Obj(kind, lane, t))
        self.safe = {k for k in range(LANES) if row.get(k) != "wall"}
        for o in extra or []:
            self.objs.append(o)

    def trail(self, t: float, lanes: list[int], kind: str = "gem", step: float = 0.2) -> float:
        for i, lane in enumerate(lanes):
            self.objs.append(Obj(kind, lane, t + i * step))
        return t + (len(lanes) - 1) * step

    # ---- patterns --------------------------------------------------------
    def pattern(self, sector: int, t: float, gap: float) -> float:
        rng = self.rng
        reach = 2 if gap >= 0.7 else 1
        weights = {
            1: {"single": 30, "pair": 18, "fence": 14, "beams": 10, "breather": 20, "gate": 8},
            2: {"pair": 18, "gate": 16, "fence": 14, "beams": 14, "slalom": 12, "mix": 12, "breather": 14},
            3: {"gate": 20, "mix": 24, "slalom": 16, "fence": 10, "beams": 10, "pair": 10, "breather": 10},
        }[sector]
        name = rng.choices(list(weights), list(weights.values()))[0]

        for _ in range(40):
            if name == "breather":
                start = rng.randrange(LANES)
                shape = rng.choice(["line", "sweep", "sky"])
                if shape == "line":
                    end = self.trail(t, [start] * 5)
                elif shape == "sweep":
                    d = 1 if start < 2 else -1
                    lanes = [min(max(start + d * (i // 2), 0), LANES - 1) for i in range(6)]
                    end = self.trail(t, lanes, step=0.26)
                else:
                    end = self.trail(t, [start] * 3, kind="sky", step=0.22)
                self.safe = set(range(LANES))
                return end + gap * 0.8

            if name == "single":
                row = {rng.randrange(LANES): "wall"}
            elif name == "pair":
                a, b = rng.sample(range(LANES), 2)
                row = {a: "wall", b: "wall"}
            elif name == "gate":
                gap_lane = rng.randrange(LANES)
                row = {k: "wall" for k in range(LANES) if k != gap_lane}
            elif name == "fence":
                n = rng.choice([3, 4, 5, 5])
                s = rng.randrange(LANES - n + 1)
                row = {k: "fence" for k in range(s, s + n)}
            elif name == "beams":
                n = rng.choice([3, 4, 5])
                s = rng.randrange(LANES - n + 1)
                row = {k: "beam" for k in range(s, s + n)}
            elif name == "mix":
                kinds = ["wall", "wall", "fence", "beam", None]
                row = {k: v for k in range(LANES) if (v := rng.choice(kinds))}
                if sum(1 for v in row.values() if v == "wall") > 3:
                    continue
            else:  # slalom: three rows of walls with a moving gap
                g = rng.randrange(LANES)
                rows = []
                for i in range(3):
                    g = min(max(g + rng.choice([-1, 1]), 0), LANES - 1)
                    rows.append({k: "wall" for k in range(LANES) if abs(k - g) >= 2 or (k != g and i == 1)})
                if not self.reachable(rows[0], reach):
                    continue
                for i, r in enumerate(rows):
                    self.put(t + i * max(gap, 0.72), r)
                return t + 2 * max(gap, 0.72) + gap

            if not self.reachable(row, reach):
                continue

            # Rewards riding along with the hazard: violet shards over fences,
            # gold shards under laser beams.
            extra: list[Obj] = []
            for lane, kind in row.items():
                if kind == "fence" and rng.random() < 0.35:
                    extra.append(Obj("sky", lane, t))
                if kind == "beam" and rng.random() < 0.3:
                    extra.append(Obj("gem", lane, t))
            # A gold shard in a free lane now and then.
            free = [k for k in range(LANES) if k not in row]
            if free and rng.random() < 0.3:
                extra.append(Obj("gem", rng.choice(free), t))
            self.put(t, row, extra)
            return t + gap
        return t + gap

    def build(self) -> "Course":
        # Tutorial: one of each hazard, with a hint shown just before it.
        self.hints += [
            (1.2, "Dodge the walls", "← → or tap left / right"),
            (4.2, "Jump the fences", "Hold Space or hold the centre"),
            (7.2, "Stay low under lasers", "Let go of jump"),
            (10.4, "Grab shards", "Gold: stay low · Violet: jump"),
        ]
        self.put(3.0, {2: "wall", 3: "wall"})
        self.put(6.0, {k: "fence" for k in range(LANES)}, [Obj("sky", 1, 6.0), Obj("sky", 3, 6.0)])
        self.put(9.0, {k: "beam" for k in range(LANES)}, [Obj("gem", 2, 9.0)])
        self.trail(12.0, [2, 2, 1, 1, 0])
        self.trail(13.6, [3, 3, 3], kind="sky", step=0.22)
        self.safe = set(range(LANES))

        t = 15.4
        while t < LAST_HAZARD:
            sector = tier_at(t)
            # A quiet stretch around each sector change.
            for s in SECTOR_AT:
                if s - 1.2 <= t < s + 2.2:
                    t = s + 2.2
                    sector = tier_at(t)
            gap = self.rng.uniform(*GAPS[sector])
            t = self.pattern(sector, t, gap)

        self.objs = [o for o in self.objs if o.hit <= LAST_HAZARD + 0.8]
        self.objs.sort(key=lambda o: (o.spawn, o.lane))
        self.check()
        return self

    def check(self) -> None:
        by_lane: dict[int, list[float]] = {k: [] for k in range(LANES)}
        for o in self.objs:
            if o.kind in HAZARD_CODE:
                by_lane[o.lane].append(o.hit)
        for lane, hits in by_lane.items():
            hits.sort()
            for a, b in zip(hits, hits[1:]):
                assert b - a > 2 * HALF + 0.05, f"hazards overlap in lane {lane} at {a:.2f}s"


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def pct(t: float, total: float) -> str:
    return f"{t / total * 100:.4f}".rstrip("0").rstrip(".") + "%"


def css(course: Course) -> str:
    out: list[str] = []
    w = out.append
    w("/* Generated by tools/course.py. Do not edit by hand. */\n")
    w("@layer course {\n")

    # 1. The collision timeline: one stepped integer per lane on <html>.
    #    0 = clear, 1 = wall, 2 = fence, 3 = laser beam.
    names = ", ".join(f"lane{k} {SCHEDULE:g}s steps(1, end) forwards" for k in range(LANES))
    w("  html:has(.lane:checked) {\n")
    w(f"    animation: {names},\n")
    w(f"      sector {SCHEDULE:g}s steps(1, end) forwards;\n  }}\n")
    for k in range(LANES):
        frames: list[tuple[float, int]] = [(0.0, 0)]
        for o in sorted((o for o in course.objs if o.lane == k and o.kind in HAZARD_CODE), key=lambda o: o.hit):
            frames.append((o.hit - HALF, HAZARD_CODE[o.kind]))
            frames.append((o.hit + HALF, 0))
        body = " ".join(f"{pct(t, SCHEDULE)}{{--l{k}:{v}}}" for t, v in frames)
        w(f"  @keyframes lane{k} {{ {body} }}\n")
    w(
        f"  @keyframes sector {{ 0%{{--sector:1}} {pct(SECTOR_AT[0], SCHEDULE)}{{--sector:2}} "
        f"{pct(SECTOR_AT[1], SCHEDULE)}{{--sector:3}} 100%{{--sector:3}} }}\n\n"
    )

    # 2. Collision: while a lane is hot and the ship is in it, the shield
    #    drain on <body> runs. <html> is the style container for <body>.
    w("  /* Collision: the shield drain on <body> only runs while you overlap a hazard. */\n")
    for k in range(LANES):
        sel = f"body:has(#l{k}:checked)"
        w(f"  @container style(--l{k}: 1) {{ {sel} {{ --hit: 1; animation-play-state: running; }} }}\n")
        w(f"  @container style(--l{k}: 2) {{ {sel}:not(:has({JUMP})) {{ --hit: 1; animation-play-state: running; }} }}\n")
        w(f"  @container style(--l{k}: 3) {{ {sel}:has({JUMP}) {{ --hit: 1; animation-play-state: running; }} }}\n")

    # 3. Flight and hit windows for each speed tier.
    w("\n  /* Flight: spawn deep in the pipe, pass the ship, fade behind the camera. */\n")
    for tier, approach in TIERS.items():
        dur = flight(tier)
        a, b = (approach - HALF) / dur * 100, (approach + HALF) / dur * 100
        w(f"  .game:has(.lane:checked) .o.v{tier} {{ animation: fly {dur:.3f}s linear var(--t), hot{tier} {dur:.3f}s steps(1, end) var(--t); }}\n")
        w(f"  @keyframes hot{tier} {{ 0% {{ --hot: 0; }} {a:.3f}% {{ --hot: 1; }} {b:.3f}% {{ --hot: 0; }} }}\n")
    w(f"  .game {{ --ring-dur: {flight(1):.3f}s; }}\n")
    w(f"  @container style(--sector: 2) {{ .game {{ --ring-dur: {flight(2):.3f}s; }} }}\n")
    w(f"  @container style(--sector: 3) {{ .game {{ --ring-dur: {flight(3):.3f}s; }} }}\n")

    # 4. Per-object latch: while this object is in its hit window and the
    #    ship is in its lane (at the right height), its 50 ms latch runs.
    w("\n  /* Per-object latch: wrecks a hazard you hit, or collects a shard. */\n")
    w("  @container style(--hot: 1) {\n")
    sels = []
    for k in range(LANES):
        g = f".game:has(#l{k}:checked)"
        sels.append(f"    {g} .o.k{k}.wall > .x")
        sels.append(f"    {g}:not(:has({JUMP})) .o.k{k}:is(.fence, .gem) > .x")
        sels.append(f"    {g}:has({JUMP}) .o.k{k}:is(.beam, .sky) > .x")
    w(",\n".join(sels))
    w(" {\n      animation-play-state: running;\n    }\n  }\n}\n")
    return "".join(out)


FACES = {
    "wall": '<i class="f fr"></i><i class="f tp"></i><i class="f sl"></i><i class="f sr"></i>',
    "fence": '<i class="f fr"></i><i class="f tp"></i>',
    "beam": '<i class="f pl"></i><i class="f pr"></i><i class="f bar"></i>',
    "gem": '<i class="f d1"></i><i class="f d2"></i>',
    "sky": '<i class="f d1"></i><i class="f d2"></i>',
}
BURST = '<i class="bu"><i></i><i></i><i></i><i></i><i></i><i></i></i>'
PTS = '<i class="pts">+100</i>'


def markup(course: Course) -> str:
    rows = []
    for o in course.objs:
        extra = PTS if o.kind in ("gem", "sky") else BURST
        pillar = '<i class="pillar"></i>' if o.kind == "sky" else ""
        rows.append(
            f'<i class="o {o.kind} k{o.lane} v{o.tier}" style="--t:{o.spawn:.3f}s">'
            f'{pillar}<i class="x"><i class="m">{FACES[o.kind]}</i>{extra}</i></i>'
        )
    return "\n".join("        " + r for r in rows)


def hints(course: Course) -> str:
    rows = []
    for t, title, sub in course.hints:
        rows.append(f'      <p class="hint" style="--at:{t:g}s"><b>{title}</b> <span>{sub}</span></p>')
    return "\n".join(rows)


def splice(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:begin -->).*?(\n[ ]*<!-- {name}:end -->)", re.S)
    assert pattern.search(text), f"marker {name} not found"
    return pattern.sub(lambda m: m.group(1) + "\n" + content + m.group(2), text)


def main() -> None:
    course = Course(SEED).build()
    (ROOT / "course.css").write_text(css(course))
    html_path = ROOT / "index.html"
    html = html_path.read_text()
    html = splice(html, "course", markup(course))
    html = splice(html, "hints", hints(course))
    html_path.write_text(html)

    kinds: dict[str, int] = {}
    for o in course.objs:
        kinds[o.kind] = kinds.get(o.kind, 0) + 1
    print(f"{len(course.objs)} objects:", ", ".join(f"{v} {k}" for k, v in sorted(kinds.items())))


if __name__ == "__main__":
    main()
