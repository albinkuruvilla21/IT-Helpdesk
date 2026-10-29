#!/usr/bin/env python3
"""
Pull the accepted design straight from Figma (REST API), so the design values come from the source, not from an
export. Writes to specs/_working/figma/ (never committed). Adapted from the Acies SPFx template.

  uv run tools/figma_pull.py pages                    every page and its top-level frames
  uv run tools/figma_pull.py pull [--png-scale 1]     the design page: node tree, a PNG per frame, frames.json and
                                                      values.md (colours, type in px and Power Apps points, radii,
                                                      shadows, gaps and paddings, scaled to the app)
  uv run tools/figma_pull.py images                   every picture the design page fills a shape with (photos, logos),
                                                      as the original files, and images.md: where each is used and at
                                                      what size. For sample data only: crop and size them for the app,
                                                      ask about their licence, never commit the originals

specs/figma.json says which design to read:

  {"file": "<file key from the URL>", "page": "<page node id>",
   "scale": 1.0,        optional: app length per Figma px (app content width / frame width). Type in points is
                        px x scale x 0.75, like tools/prototype_design.py; radii, gaps and paddings are px x scale
   "minWidth": 320}     optional: frames narrower than this are parts, not screens (a phone frame is 360-430)

The token is a personal access token with the read-only "File content" scope, from $FIGMA_TOKEN or
~/.config/figma/token. It is a secret (D7): never in the repository, a command line or a log.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "specs" / "figma.json"
OUT = ROOT / "specs" / "_working" / "figma"
API = "https://api.figma.com/v1"


def config() -> dict:
    if not CONFIG.exists():
        sys.exit(f"No {CONFIG.as_posix()}: write {{\"file\": \"<file key>\", \"page\": \"<page node id>\"}} (inputs/README.md, The design)")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg.setdefault("scale", 1.0)
    cfg.setdefault("minWidth", 320)
    return cfg


def token() -> str:
    t = os.environ.get("FIGMA_TOKEN", "").strip()
    f = Path.home() / ".config" / "figma" / "token"
    if not t and f.exists():
        t = f.read_text(encoding="utf-8").strip()
    if not t:
        sys.exit("No Figma token: set FIGMA_TOKEN or write it to ~/.config/figma/token")
    return t


def get(path: str, **params) -> dict:
    url = f"{API}{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    req = urllib.request.Request(url, headers={"X-Figma-Token": token()})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Figma {e.code} on {path}: {e.read().decode('utf-8', 'replace')[:200]}")


def download(url: str, dest: Path, tries: int = 3) -> None:
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                dest.write_bytes(r.read())
            return
        except urllib.error.URLError:
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "frame"


def hexa(c: dict, opacity: float = 1) -> str:
    rgb = "#" + "".join(f"{round(c[k] * 255):02X}" for k in "rgb")
    a = round(c.get("a", 1) * opacity, 2)
    return rgb if a >= 1 else f"{rgb} @{a}"


def num(v: float) -> str:
    return f"{round(v, 1):g}"


def walk(node: dict, acc: dict, scale: float) -> None:
    """Tallies the values the app's tokens and screens use: fills, strokes, type, radii, effects, auto-layout spacing."""
    if node.get("visible") is False:
        return
    for key, bucket in (("fills", "fill"), ("strokes", "stroke")):
        for p in node.get(key) or []:
            if p.get("visible") is not False and p.get("type") == "SOLID":
                acc[bucket][hexa(p["color"], p.get("opacity", 1))] += 1
    if node.get("type") == "TEXT":
        s = node.get("style", {})
        size, lh = s.get("fontSize") or 0, s.get("lineHeightPx")
        acc["type"][
            f"{s.get('fontFamily')} {num(size)}px = {num(size * scale * 0.75)}pt"
            + (f" / line {num(lh * scale)}" if lh else "") + f" w{s.get('fontWeight')}"
            + (f" {s['textCase'].lower()}" if s.get("textCase") else "")
        ] += 1
    if node.get("cornerRadius"):
        acc["radius"][num(node["cornerRadius"] * scale)] += 1
    for e in node.get("effects") or []:
        if e.get("visible") is not False and "SHADOW" in e.get("type", ""):
            o = e.get("offset", {})
            acc["effect"][f"{e['type'].lower()} {num(o.get('x', 0) * scale)} {num(o.get('y', 0) * scale)} "
                          f"{num(e.get('radius', 0) * scale)} {num(e.get('spread', 0) * scale)} {hexa(e['color'])}"] += 1
    if node.get("layoutMode") in ("HORIZONTAL", "VERTICAL"):
        acc["gap"][num(node.get("itemSpacing", 0) * scale)] += 1
        pads = tuple(node.get(k, 0) for k in ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft"))
        if any(pads):
            acc["padding"][" ".join(num(p * scale) for p in pads)] += 1
    for c in node.get("children") or []:
        walk(c, acc, scale)


def screens(children: list, min_width: float) -> list:
    return [c for c in children if c["type"] == "FRAME" and (c.get("absoluteBoundingBox") or {}).get("width", 0) >= min_width]


def pages() -> int:
    cfg = config()
    d = get(f"/files/{cfg['file']}", depth=2)
    print(f"{d['name']} (last modified {d['lastModified']})")
    for p in d["document"]["children"]:
        print(f"\n{p['id']}  {p['name']}" + ("   <- design page" if p["id"] == cfg["page"] else ""))
        for c in screens(p.get("children", []), cfg["minWidth"]):
            b = c["absoluteBoundingBox"]
            print(f"  {c['id']:>10}  {c['name']:<28} {b['width']:.0f} x {b['height']:.0f}")
    return 0


def pull(png_scale: float) -> int:
    cfg = config()
    scale = float(cfg["scale"])
    OUT.mkdir(parents=True, exist_ok=True)
    tree = get(f"/files/{cfg['file']}/nodes", ids=cfg["page"])["nodes"][cfg["page"]]
    (OUT / "page.json").write_text(json.dumps(tree, indent=1), encoding="utf-8")
    styles = get(f"/files/{cfg['file']}/styles")
    (OUT / "styles.json").write_text(json.dumps(styles, indent=1), encoding="utf-8")

    frames = screens(tree["document"].get("children", []), cfg["minWidth"])
    names, seen = {}, Counter()
    for f in frames:
        base = slug(f["name"])
        seen[base] += 1
        names[f["id"]] = base if seen[base] == 1 else f"{base}-{seen[base]}"

    urls = get(f"/images/{cfg['file']}", ids=",".join(names), format="png", scale=png_scale)["images"] if names else {}
    summary = ["# Figma design values", "",
               f"File `{cfg['file']}`, page `{cfg['page']}`. Scale {num(scale)}: type is px x scale x 0.75 = points; "
               "radii, gaps, paddings and shadows are px x scale. A proposal for /design-spec, which confirms each value.", ""]
    for f in frames:
        name = names[f["id"]]
        if urls.get(f["id"]):
            download(urls[f["id"]], OUT / f"{name}.png")
        acc = {k: Counter() for k in ("fill", "stroke", "type", "radius", "effect", "gap", "padding")}
        walk(f, acc, scale)
        b = f["absoluteBoundingBox"]
        summary += [f"## {f['name']} (`{f['id']}`, {b['width']:.0f} x {b['height']:.0f}) -> {name}.png", ""]
        for k, c in acc.items():
            if c:
                summary.append(f"- **{k}**: " + "; ".join(f"{v} x{n}" for v, n in c.most_common()))
        summary.append("")
        print(f"{name:<32} {f['id']}")
    (OUT / "values.md").write_text("\n".join(summary), encoding="utf-8")
    (OUT / "frames.json").write_text(json.dumps({f["id"]: {
        "name": f["name"], "png": f"{names[f['id']]}.png", "x": f["absoluteBoundingBox"]["x"], "y": f["absoluteBoundingBox"]["y"],
        "w": f["absoluteBoundingBox"]["width"], "h": f["absoluteBoundingBox"]["height"]} for f in frames}, indent=1), encoding="utf-8")
    print(f"\n{len(frames)} frames -> {OUT.relative_to(ROOT)}/ (page.json, styles.json, values.md, frames.json, *.png)")
    return 0


def images() -> int:
    """The design page's image fills, as uploaded to Figma, with where each one is drawn."""
    cfg = config()
    tree = get(f"/files/{cfg['file']}/nodes", ids=cfg["page"])["nodes"][cfg["page"]]["document"]
    frames = {c["id"]: c["name"] for c in tree.get("children", []) if c["type"] == "FRAME"}
    used: dict = {}

    def visit(n, frame):
        if n.get("visible") is False:
            return
        frame = frames.get(n["id"], frame)
        b = n.get("absoluteBoundingBox") or {}
        for p in n.get("fills") or []:
            if p.get("type") == "IMAGE" and p.get("visible") is not False and p.get("imageRef"):
                used.setdefault(p["imageRef"], []).append(f"{frame or 'page'}: {n['name']} {b.get('width', 0):.0f} x {b.get('height', 0):.0f} "
                                                          f"({p.get('scaleMode', 'FILL').lower()})")
        for c in n.get("children") or []:
            visit(c, frame)

    visit(tree, None)
    out = OUT / "images"
    out.mkdir(parents=True, exist_ok=True)
    urls = get(f"/files/{cfg['file']}/images")["meta"]["images"]
    lines = ["# Figma image fills", "", "| File | Drawn at |", "|---|---|"]
    for ref, where in used.items():
        if urls.get(ref):
            download(urls[ref], out / ref)
            lines.append(f"| `{ref}` | {'; '.join(sorted(set(where))[:6])}{' ...' if len(set(where)) > 6 else ''} |")
    (out / "images.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(used)} pictures -> {out.relative_to(ROOT)}/ (images.md says where each is drawn)")
    return 0


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pages")
    sub.add_parser("images")
    p = sub.add_parser("pull")
    p.add_argument("--png-scale", type=float, default=1, help="PNG resolution only; keep 1 so a PNG's pixels are the design's")
    a = ap.parse_args(argv)
    return pages() if a.cmd == "pages" else images() if a.cmd == "images" else pull(a.png_scale)


if __name__ == "__main__":
    sys.exit(main())
