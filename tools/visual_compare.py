#!/usr/bin/env python3
"""
Measure the accepted prototype in a real browser, and compare each screen with a screenshot of it in Studio (G3, G7).

  uv run tools/visual_compare.py measure scrHome [--state ready] [--scheme light]   the prototype's rendered values for one
                                                                                    screen of the map: build to these
  uv run tools/visual_compare.py measure --html <file> --region <css> [--width 1366] [--setup <js>] [--scheme dark]
                                                                                    the same, for any page and region
  uv run tools/visual_compare.py run [--only scrHome scrNew] [--strict]             render every mapped view, and compare it
                                                                                    with its Studio screenshot
  uv run tools/visual_compare.py compare <design.png> <screenshot.png> [--out FILE] two images, without a map

WHY. tools/prototype_design.py reads the prototype's CSS as text: it can't apply the cascade or inheritance, and it
doesn't see a view that a script draws. Here Chromium renders the prototype, so each value is what the browser actually
shows, per view, region, state and colour scheme. A canvas app can't be rendered outside Power Apps, so the build side
is a screenshot a person takes in Studio; the comparison makes "Matched" in the fidelity register evidence, not an
impression.

The map, specs/visual-map.json (written by /design-spec at G3, completed by /ui-dev at G7):

  {
    "width": 1366, "height": 768,       the browser window the prototype is drawn for
    "scale": 1.0,                       app length per prototype px: type in points is px x scale x 0.75, lengths px x scale
                                        (the same scale as tools/prototype_design.py and specs/figma.json)
    "clock": "2026-10-28T09:00:00",     optional: the time the prototype sees, so dates and greetings read the same each run
    "tolerance": 0.08,                  share of differing pixels still called a match (fonts render differently in Studio)
    "settleMs": 300,                    wait after load and after "setup", for scripts and fonts
    "screens": [
      { "screen": "scrHome", "state": "ready", "scheme": "light",
        "design": "inputs/design/prototype.html", "region": "#app",
        "setup": "showView('home')",    optional JavaScript run after load: open the view, fill a state
        "screenshot": "specs/screenshots/scrHome-ready-light.png",
        "accepted": "design-spec §9 DEV-02: …" }   optional: why a difference above the tolerance is allowed
    ]
  }

Screenshots are of the app's canvas only (Studio's Preview, F5, or the published app; no Studio chrome), at the app's
size, in the state and scheme the entry names. They are committed in specs/screenshots/: the evidence for "Matched".
Output: specs/_working/visual/ (report.md, report.json, design PNGs, comparison sheets). Working files: never committed.
Needs: the packages in pyproject.toml (uv run installs them), and `uv run playwright install chromium` once per machine.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP = ROOT / "specs" / "visual-map.json"
OUT = ROOT / "specs" / "_working" / "visual"
PIXEL_THRESHOLD = 40  # 0-255 grey difference counted as a different pixel: above anti-aliasing, below a real colour change
ASPECT_SLACK = 0.03
DEFAULTS = {"width": 1366, "height": 768, "scale": 1.0, "clock": None, "tolerance": 0.08, "settleMs": 300}

FREEZE_CSS = "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}"

MEASURE_JS = r"""
(sel) => {
  const root = document.querySelector(sel);
  if (!root) return null;
  const R = root.getBoundingClientRect();
  const round = (v) => Math.round(v * 10) / 10;
  const rel = (r) => ({ x: round(r.left - R.left), y: round(r.top - R.top), w: round(r.width), h: round(r.height) });
  const shown = (el) => {
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    return r.width > 1 && r.height > 1 && cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0';
  };
  const clear = 'rgba(0, 0, 0, 0)';
  const behind = (e) => {
    for (let p = e.parentElement; p; p = p.parentElement) {
      const c = getComputedStyle(p).backgroundColor;
      if (c !== clear) return c;
    }
    return 'rgb(255, 255, 255)';
  };
  const sides = ['Top', 'Right', 'Bottom', 'Left'];
  const texts = [], boxes = [];
  for (const el of [root, ...root.querySelectorAll('*')]) {
    if (!shown(el)) continue;
    const cs = getComputedStyle(el);
    const own = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(' ').replace(/\s+/g, ' ').trim();
    const value = (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') ? (el.value || el.placeholder || '') : '';
    const text = own || value;
    if (text) {
      texts.push(Object.assign(rel(el.getBoundingClientRect()), {
        text: text.slice(0, 60), tag: el.tagName.toLowerCase(), fontFamily: cs.fontFamily.split(',')[0].replace(/["']/g, '').trim(),
        fontSize: parseFloat(cs.fontSize), fontWeight: cs.fontWeight, lineHeight: cs.lineHeight, color: cs.color,
        textAlign: cs.textAlign
      }));
    }
    const borders = sides.filter((s) => parseFloat(cs['border' + s + 'Width']) > 0 && cs['border' + s + 'Style'] !== 'none');
    const decorated = (cs.backgroundColor !== clear && cs.backgroundColor !== behind(el)) || cs.boxShadow !== 'none' ||
      borders.length > 0 || cs.backgroundImage !== 'none';
    if (decorated) {
      boxes.push(Object.assign(rel(el.getBoundingClientRect()), {
        tag: el.tagName.toLowerCase(), id: el.id || '', cls: (el.className && el.className.baseVal === undefined ? el.className : '').toString().slice(0, 40),
        backgroundColor: cs.backgroundColor, backgroundImage: cs.backgroundImage === 'none' ? '' : cs.backgroundImage.slice(0, 80),
        borderRadius: cs.borderTopLeftRadius, border: borders.length ? `${cs.borderTopWidth} ${cs.borderTopColor} (${borders.join(',').toLowerCase()})` : '',
        boxShadow: cs.boxShadow === 'none' ? '' : cs.boxShadow, padding: sides.map((s) => cs['padding' + s]).join(' '),
        opacity: cs.opacity
      }));
    }
  }
  return { region: rel(R), texts, boxes };
}
"""


# ─── The map ──────────────────────────────────────────────────────────────────

def load_map(path: Path = None) -> dict:
    path = path or MAP
    if not path.exists():
        sys.exit(f"No {path.as_posix()}: /design-spec writes it (G3). The format is in this tool's help (--help).")
    cfg = {**DEFAULTS, **json.loads(path.read_text(encoding="utf-8"))}
    for e in cfg.get("screens", []):
        for key in ("screen", "design", "region"):
            if not e.get(key):
                sys.exit(f"{path.name}: a screen entry has no '{key}': {json.dumps(e)[:120]}")
        e.setdefault("state", "ready")
        e.setdefault("scheme", "light")
    return cfg


def entry_id(e: dict) -> str:
    return f"{e['screen']}-{e['state']}-{e['scheme']}"


def pick(cfg: dict, screen: str, state: str | None, scheme: str | None) -> dict:
    found = [e for e in cfg.get("screens", []) if e["screen"] == screen and (state is None or e["state"] == state)
             and (scheme is None or e["scheme"] == scheme)]
    if not found:
        sys.exit(f"No entry for {screen} {state or ''} {scheme or ''} in the map")
    return found[0]


# ─── Browser ──────────────────────────────────────────────────────────────────

class Browser:
    def __enter__(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            sys.exit("playwright is not installed. Run the tools through uv (uv run tools/visual_compare.py), "
                     "then uv run playwright install chromium once.")
        self.pw = sync_playwright().start()
        try:
            self.browser = self.pw.chromium.launch()
        except Exception as exc:  # Chromium not downloaded yet
            self.pw.stop()
            sys.exit(f"Chromium can't start ({str(exc).splitlines()[0]}). Run: uv run playwright install chromium")
        return self

    def open(self, html: Path, cfg: dict, e: dict):
        """The prototype in a fresh page: the window size, scheme and clock the map says, then the entry's setup."""
        page = self.browser.new_page(viewport={"width": int(cfg["width"]), "height": int(cfg["height"])},
                                     color_scheme=e.get("scheme", "light"), device_scale_factor=1)
        if cfg.get("clock"):
            page.clock.set_fixed_time(dt.datetime.fromisoformat(cfg["clock"]))
        page.goto(html.resolve().as_uri(), wait_until="load")
        page.add_style_tag(content=FREEZE_CSS)
        page.evaluate("document.fonts.ready.then(() => true)")
        if e.get("setup"):
            page.evaluate(f"() => {{ {e['setup']}; }}")
        page.wait_for_timeout(int(cfg["settleMs"]))
        return page

    def __exit__(self, *exc):
        self.browser.close()
        self.pw.stop()


def design_path(e: dict) -> Path:
    p = Path(e["design"])
    p = p if p.is_absolute() else ROOT / p
    if not p.exists():
        sys.exit(f"{entry_id(e)}: the design file {e['design']} doesn't exist")
    return p


def measure_entry(b: Browser, cfg: dict, e: dict) -> dict:
    page = b.open(design_path(e), cfg, e)
    found = page.evaluate(MEASURE_JS, e["region"])
    page.close()
    if found is None:
        sys.exit(f"{entry_id(e)}: no element matches the region '{e['region']}' (after setup)")
    return found


def render_entry(b: Browser, cfg: dict, e: dict, out: Path) -> Path:
    page = b.open(design_path(e), cfg, e)
    loc = page.locator(e["region"]).first
    if loc.count() == 0:
        sys.exit(f"{entry_id(e)}: no element matches the region '{e['region']}' (after setup)")
    out.parent.mkdir(parents=True, exist_ok=True)
    loc.screenshot(path=str(out))
    page.close()
    return out


def shown(p: Path) -> str:
    """A path as the user would type it: relative to the repository when it is inside it."""
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


# ─── Units ────────────────────────────────────────────────────────────────────

def px(v) -> float | None:
    m = re.match(r"^(-?[\d.]+)px$", str(v).strip())
    return float(m.group(1)) if m else None


def scaled(v, scale: float) -> str:
    """'16px 8px' at scale 0.5 -> '8 4' (app lengths); other values unchanged."""
    out = []
    for part in str(v).split():
        n = px(part)
        out.append(f"{round(n * scale, 1):g}" if n is not None else part)
    return " ".join(out)


def hexcolour(v: str) -> str:
    m = re.match(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)", str(v))
    if not m:
        return str(v)
    r, g, b = (round(float(x)) for x in m.groups()[:3])
    a = float(m.group(4)) if m.group(4) is not None else 1.0
    return f"#{r:02X}{g:02X}{b:02X}" + ("" if a >= 1 else f" @{round(a, 2):g}")


def to_app(found: dict, scale: float) -> dict:
    """The rendered values in the app's units: type in points, lengths scaled (design-standards §3, ui-patterns §10)."""
    texts = [{
        "text": t["text"], "font": t["fontFamily"], "px": t["fontSize"], "pt": round(t["fontSize"] * scale * 0.75, 1),
        "weight": t["fontWeight"], "lineHeight": scaled(t["lineHeight"], scale), "color": hexcolour(t["color"]),
        "align": t["textAlign"], "x": round(t["x"] * scale, 1), "y": round(t["y"] * scale, 1),
        "w": round(t["w"] * scale, 1), "h": round(t["h"] * scale, 1)} for t in found["texts"]]
    boxes = [{
        "box": f"{b['tag']}{'#' + b['id'] if b['id'] else ''}{'.' + b['cls'].split()[0] if b['cls'].strip() else ''}",
        "fill": hexcolour(b["backgroundColor"]), "image": b["backgroundImage"], "radius": scaled(b["borderRadius"], scale),
        "border": b["border"], "shadow": scaled(b["boxShadow"], scale), "padding": scaled(b["padding"], scale), "opacity": b["opacity"],
        "x": round(b["x"] * scale, 1), "y": round(b["y"] * scale, 1), "w": round(b["w"] * scale, 1), "h": round(b["h"] * scale, 1)}
        for b in found["boxes"]]
    reg = found["region"]
    return {"scale": scale, "region": {k: round(reg[k] * scale, 1) for k in ("w", "h")}, "texts": texts, "boxes": boxes}


def measure_markdown(name: str, values: dict) -> str:
    cell = lambda v: str(v).replace("|", "\\|")
    lines = [f"# {name}", "", f"Rendered in Chromium; app units at scale {values['scale']:g} (type in points, lengths scaled). "
             f"Region {values['region']['w']:g} x {values['region']['h']:g}.", "",
             "## Text", "", "| Text | Font | px → pt | Weight | Line | Colour | Align | x, y | w x h |", "|---|---|---|---|---|---|---|---|---|"]
    for t in values["texts"]:
        lines.append(f"| {cell(t['text'])} | {t['font']} | {t['px']:g} → {t['pt']:g} | {t['weight']} | {t['lineHeight']} | {t['color']} "
                     f"| {t['align']} | {t['x']:g}, {t['y']:g} | {t['w']:g} x {t['h']:g} |")
    lines += ["", "## Boxes", "", "| Box | Fill | Radius | Border | Shadow | Padding | x, y | w x h |", "|---|---|---|---|---|---|---|---|"]
    for b in values["boxes"]:
        fill = b["fill"] + (f" + {b['image'][:40]}" if b["image"] else "")
        lines.append(f"| {cell(b['box'])} | {cell(fill)} | {b['radius']} | {cell(b['border'])} | {cell(b['shadow'])} | {b['padding']} "
                     f"| {b['x']:g}, {b['y']:g} | {b['w']:g} x {b['h']:g} |")
    return "\n".join(lines) + "\n"


# ─── Images ───────────────────────────────────────────────────────────────────

def compare_images(design_png: Path, shot_png: Path, out_png: Path) -> dict:
    """Share of differing pixels, the screenshot resized to the design's size; writes design | screenshot | difference."""
    from PIL import Image, ImageChops, ImageDraw

    a, b = Image.open(design_png).convert("RGB"), Image.open(shot_png).convert("RGB")
    aspect = abs((b.width / b.height) / (a.width / a.height) - 1)
    original = f"{b.width} x {b.height}"
    if b.size != a.size:
        b = b.resize(a.size, Image.LANCZOS)
    w, h = a.size
    mask = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > PIXEL_THRESHOLD else 0)
    share = mask.histogram()[255] / (w * h)
    overlay = Image.blend(b.convert("L").convert("RGB"), Image.new("RGB", (w, h), "white"), 0.6)
    overlay.paste(Image.new("RGB", (w, h), (220, 0, 0)), (0, 0), mask)

    gap, head = 16, 24
    sheet = Image.new("RGB", (w * 3 + gap * 2, h + head), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (im, title) in enumerate(((a, "Prototype"), (b, f"Studio ({original})"), (overlay, f"Difference ({share:.1%} of pixels)"))):
        x = i * (w + gap)
        draw.text((x, 6), title, fill=(0, 0, 0))
        sheet.paste(im, (x, head))
    out_png.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_png)
    return {"share": round(share, 4), "aspect": round(aspect, 4), "design": f"{w} x {h}", "screenshot": original}


def verdict(e: dict, result: dict | None, tolerance: float) -> str:
    if result is None:
        return "no screenshot"
    if result["aspect"] > ASPECT_SLACK:
        return "accepted" if e.get("accepted") else "differs"  # a different shape: the layout itself differs
    if result["share"] <= tolerance:
        return "matches"
    return "accepted" if e.get("accepted") else "differs"


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_measure(a) -> int:
    if a.html:
        cfg = {**DEFAULTS, "width": a.width, "height": a.height, "scale": a.scale, "clock": a.clock}
        e = {"screen": Path(a.html).stem, "state": "ready", "scheme": a.scheme, "design": a.html, "region": a.region, "setup": a.setup}
    else:
        cfg = load_map(a.map)
        e = pick(cfg, a.screen, a.state, a.scheme)
    with Browser() as b:
        values = to_app(measure_entry(b, cfg, e), float(cfg["scale"]))
    name = entry_id(e)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.measure.json").write_text(json.dumps(values, indent=1, ensure_ascii=False), encoding="utf-8")
    md = measure_markdown(name, values)
    (OUT / f"{name}.measure.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"Written: {shown(OUT / (name + '.measure.md'))} and .json")
    return 0


def cmd_run(a) -> int:
    cfg = load_map(a.map)
    entries = [e for e in cfg.get("screens", []) if not a.only or e["screen"] in a.only]
    if not entries:
        sys.exit("No screens to compare (check --only and the map's 'screens')")
    rows, results = [], []
    with Browser() as b:
        for e in entries:
            name = entry_id(e)
            design = render_entry(b, cfg, e, OUT / f"{name}.prototype.png")
            shot = (ROOT / e["screenshot"]) if e.get("screenshot") else None
            result = compare_images(design, shot, OUT / f"{name}.compare.png") if shot and shot.exists() else None
            v = verdict(e, result, float(cfg["tolerance"]))
            results.append({"entry": name, "verdict": v, **(result or {}), "accepted": e.get("accepted", "")})
            share = f"{result['share']:.1%}" if result else "—"
            aspect = f"{result['aspect']:.1%}" if result else "—"
            note = e.get("accepted", "") if v == "accepted" else (f"take {e.get('screenshot') or 'specs/screenshots/' + name + '.png'}"
                                                                    if v == "no screenshot" else "")
            rows.append(f"| {name} | {v} | {share} | {aspect} | {note} |")
            print(f"{v:<14} {name}  pixels {share}  shape {aspect}")
    OUT.mkdir(parents=True, exist_ok=True)
    counts = {k: sum(r["verdict"] == k for r in results) for k in ("matches", "accepted", "differs", "no screenshot")}
    report = ["# Prototype ↔ Studio comparison", "",
              f"Tolerance {float(cfg['tolerance']):.0%} of pixels; shape (aspect ratio) within {ASPECT_SLACK:.0%}. "
              "Look at every `*.compare.png`: a share under the tolerance can still hide a wrong word or a wrong colour.", "",
              "| Screen · state · scheme | Verdict | Pixels differing | Shape differs | Note |", "|---|---|---|---|---|", *rows, "",
              " · ".join(f"{k}: {n}" for k, n in counts.items()), ""]
    (OUT / "report.md").write_text("\n".join(report), encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n{' · '.join(f'{k}: {n}' for k, n in counts.items())}. Report: {shown(OUT / 'report.md')}")
    if a.strict and (counts["differs"] or counts["no screenshot"]):
        print("--strict: every screen needs a screenshot that matches, or an accepted deviation.")
        return 1
    return 0


def cmd_compare(a) -> int:
    out = Path(a.out) if a.out else OUT / f"{Path(a.design).stem}-vs-{Path(a.screenshot).stem}.png"
    r = compare_images(Path(a.design), Path(a.screenshot), out)
    print(f"pixels differing {r['share']:.1%}, shape differs {r['aspect']:.1%} (design {r['design']}, screenshot {r['screenshot']}). Sheet: {out}")
    return 0


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", type=Path, default=None, help="the visual map (default specs/visual-map.json)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("screen", nargs="?")
    m.add_argument("--state")
    m.add_argument("--scheme")
    m.add_argument("--html")
    m.add_argument("--region", default="body")
    m.add_argument("--setup")
    m.add_argument("--width", type=int, default=DEFAULTS["width"])
    m.add_argument("--height", type=int, default=DEFAULTS["height"])
    m.add_argument("--scale", type=float, default=1.0)
    m.add_argument("--clock")
    r = sub.add_parser("run")
    r.add_argument("--only", nargs="+")
    r.add_argument("--strict", action="store_true")
    c = sub.add_parser("compare")
    c.add_argument("design")
    c.add_argument("screenshot")
    c.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "measure":
        if not a.html and not a.screen:
            ap.error("measure needs a screen from the map, or --html <file> --region <css>")
        if a.html and not a.scheme:
            a.scheme = "light"
        return cmd_measure(a)
    return cmd_run(a) if a.cmd == "run" else cmd_compare(a)


if __name__ == "__main__":
    sys.exit(main())
