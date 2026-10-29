"""prototype_design: read an HTML prototype's CSS and turn its visual design into the values a canvas app needs.

WHY THIS EXISTS. On the first projects the app was built with the reference app's numbers (title 20, body 12, square cards, a flat header)
and its colours were picked by hand, so it looked nothing like the accepted prototype. The prototype IS the specification (CLAUDE.md §7):
its colours in BOTH schemes, its type scale, radii, spacing, shadows and background are measured here, not guessed.

What it extracts (from every <style> block, @media and @supports included):
  * CSS custom properties of :root (light) and of :root inside @media (prefers-color-scheme: dark) (dark);
  * colours resolved (var() followed, rgba() composited over the page background for the contrast checks, alpha kept for translucent fills);
  * a token proposal: each custom property mapped to a canvas token name (design-standards §3) by its name, light and dark values,
    contrast of every text token on its surface, and the nearest compliant shade where a pair fails WCAG 2.1 AA (design-spec §8);
  * the type scale: every font-size (font shorthand included) with its selector, converted to Power Apps points at the app's scale,
    with the label height the text needs (text_h);
  * radii, paddings, gaps, heights, widths, shadows and gradients per selector, scaled to the app;
  * the font stack and the first font Power Apps offers.

Sizes: Power Apps' Size is in points (1 pt = 4/3 px). A prototype laid out for a CONTENT width of W px, built into an app whose content is
C wide, scales by C / W; a CSS px becomes   pt = px * (C / W) * 0.75.   Geometry (padding, radius, height) scales by C / W.

    uv run tools/prototype_design.py inputs/design/<file>.html --content 1020 [--out specs/prototype-design.json] [--formulas]
    uv run tools/prototype_design.py inputs/design/<file>.html --content 1020 --check canvas/<App>/Src/App.pa.yaml    (/verify check 20)
    uv run tools/prototype_design.py --selftest

The output is a PROPOSAL for /design-spec, which confirms each mapping, records it in design-spec §2-§4 and writes App.Formulas.
"""
import json
import math
import re
import sys
from pathlib import Path

# Fonts Power Apps offers (the Font enumeration). System stacks map to Segoe UI, the Windows system font.
PA_FONTS = ["Segoe UI", "Open Sans", "Lato", "Arial", "Courier New", "Dancing Script", "Georgia", "Great Vibes", "Lato Black", "Lato Hairline",
            "Lato Light", "Open Sans Condensed", "Patrick Hand", "Patrick Hand SC", "Sacramento", "Verdana", "Helvetica", "Tahoma",
            "Times New Roman", "Trebuchet MS", "Lucida Console", "Lucida Sans Unicode", "Gill Sans"]
SYSTEM_FONTS = {"-apple-system", "blinkmacsystemfont", "system-ui", "sans-serif", "ui-sans-serif"}
NAMED = {"white": (255, 255, 255, 1.0), "black": (0, 0, 0, 1.0), "transparent": (0, 0, 0, 0.0)}

# CSS custom-property name -> canvas token (design-standards §3). First match wins; order matters.
TOKEN_RULES = [
    (r"^(text|fg|foreground|ink)$", "ColorText"), (r"(muted|subtle|secondary-text|text-2)", "ColorTextMuted"),
    (r"^(blue2|primary-?hover|accent-?hover|brand-?hover)$", "ColorPrimaryHover"), (r"^(blue|primary|brand|accent)$", "ColorPrimary"),
    (r"^(okbg|success-?bg|success-?fill|green-?bg)$", "ColorSuccessFill"), (r"^(ok|success|green)$", "ColorSuccess"),
    (r"^(errbg|error-?bg|danger-?bg|red-?bg)$", "ColorErrorFill"), (r"^(err|error|danger|red)$", "ColorError"),
    (r"^(warnbg|warning-?bg)$", "ColorWarningFill"), (r"^(warn|warning|amber)$", "ColorWarning"),
    (r"^(infobg|info-?bg)$", "ColorInfoFill"), (r"^(info)$", "ColorInfo"),
    (r"^(neubg|neutral-?bg)$", "ColorNeutralFill"), (r"^(neu|neutral)$", "ColorNeutralText"),
    (r"^(base|bg|background|page)$", "ColorBackground"), (r"^(glass2|surface|card|panel)$", "ColorSurface"), (r"^(glass)$", "ColorGlass"),
    (r"^(stroke)$", "ColorGlassStroke"), (r"^(hair|border|line|divider)$", "ColorDivider"), (r"^(field|input)$", "ColorField"),
    (r"^(seg|segment|track)$", "ColorSegment"), (r"^(segon|segment-?on)$", "ColorSegmentOn"),
    (r"^b(\d)$", r"ColorBackdrop\1"),
    # short names a hand-written prototype often uses: --ac, --ah, --as, --c, --bd, --tx, --mu, --h, --h2, --h3, --ln
    (r"^ac$", "ColorPrimary"), (r"^ah$", "ColorPrimaryHover"), (r"^as$", "ColorPrimaryTint"), (r"^c$", "ColorSurface"), (r"^bd$", "ColorDivider"),
    (r"^tx$", "ColorText"), (r"^mu$", "ColorTextMuted"), (r"^h$", "ColorHover"), (r"^h2$", "ColorRowHover"), (r"^h3$", "ColorSunken"), (r"^ln$", "ColorLine"),
]
# Text tokens and the surface they are read on (contrast 4.5:1), and boundary tokens (3:1).
TEXT_ON = {"ColorText": "ColorSurface", "ColorTextMuted": "ColorBackground", "ColorPrimary": "ColorSurface", "ColorSuccess": "ColorSuccessFill",
           "ColorError": "ColorErrorFill", "ColorWarning": "ColorWarningFill", "ColorInfo": "ColorInfoFill", "ColorNeutralText": "ColorNeutralFill"}


# ------------------------------------------------------------------ CSS
def css_of(html):
    return "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))


def parse_css(css):
    """[{selector, media, decls}] for every rule; @media/@supports conditions are kept in `media`."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules = []

    def walk(s, media):
        i, n = 0, len(s)
        while i < n:
            j = s.find("{", i)
            if j < 0:
                return
            sel = s[i:j].strip()
            depth, k = 1, j + 1
            while k < n and depth:
                depth += {"{": 1, "}": -1}.get(s[k], 0)
                k += 1
            body = s[j + 1:k - 1]
            if sel.startswith(("@media", "@supports")):
                walk(body, (media + " and " if media else "") + re.sub(r"\s+", "", sel))
            elif not sel.startswith("@"):
                decls = {}
                for d in re.split(r";(?![^(]*\))", body):
                    if ":" in d:
                        p, v = d.split(":", 1)
                        decls[p.strip()] = v.strip()
                for one in re.split(r",(?![^(]*\))", sel):
                    rules.append({"selector": one.strip(), "media": media, "decls": decls})
            i = k
    walk(css, "")
    return rules


# a dark scheme switched in markup rather than by the device: [data-theme=dark], :root[data-theme="dark"], html.dark, .dark, :root.dark
DARK_SELECTOR = re.compile(r"""^(?::root|html|body)?(?:\[data-(?:theme|mode|color-scheme)=["']?dark["']?\]|\.dark(?:-theme|-mode)?)$""")


def custom_properties(rules):
    light, dark = {}, {}
    for r in rules:
        target = None
        if r["selector"] == ":root":
            target = dark if "prefers-color-scheme:dark" in r["media"] else light if not r["media"] else None
        elif DARK_SELECTOR.match(r["selector"].replace(" ", "")) and not r["media"]:
            target = dark
        if target is not None:
            target.update({k[2:]: v for k, v in r["decls"].items() if k.startswith("--")})
    return light, dark


def resolve(value, props, fallback_props=None):
    for _ in range(10):
        m = re.search(r"var\(--([\w-]+)\s*(?:,\s*([^()]*))?\)", value)
        if not m:
            break
        name = m.group(1)
        rep = props.get(name, (fallback_props or {}).get(name, m.group(2) or ""))
        value = value[:m.start()] + rep + value[m.end():]
    return value.strip()


# ------------------------------------------------------------------ colour
def color(v):
    """(r, g, b, a) from #rgb, #rrggbb, #rrggbbaa, rgb(), rgba() or a few names; None for anything else."""
    v = (v or "").strip().lower()
    if v in NAMED:
        return NAMED[v]
    m = re.fullmatch(r"#([0-9a-f]{3,8})", v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        return (r, g, b, round(int(h[6:8], 16) / 255, 3) if len(h) == 8 else 1.0)
    m = re.fullmatch(r"rgba?\(([^)]*)\)", v)
    if m:
        parts = [p for p in re.split(r"[\s,/]+", m.group(1).strip()) if p]
        if len(parts) >= 3:
            r, g, b = (float(p[:-1]) * 2.55 if p.endswith("%") else float(p) for p in parts[:3])
            a = float(parts[3][:-1]) / 100 if len(parts) > 3 and parts[3].endswith("%") else float(parts[3]) if len(parts) > 3 else 1.0
            return (round(r), round(g), round(b), a)
    return None


def composite(c, over):
    a = c[3]
    return tuple(round(c[i] * a + over[i] * (1 - a)) for i in range(3)) + (1.0,)


def hexs(c):
    return "#%02x%02x%02x" % tuple(c[:3])


def rgba_fx(c):
    a = c[3]
    return f"RGBA({c[0]}, {c[1]}, {c[2]}, {int(a) if a in (0, 1) else round(a, 3)})"


def lum(c):
    def f(x):
        x /= 255
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def contrast(a, b):
    hi, lo = sorted([lum(a), lum(b)], reverse=True)
    return round((hi + 0.05) / (lo + 0.05), 2)


def compliant(fg, bg, target=4.5):
    """The nearest shade of fg's hue that reaches `target` on bg: darker on a light background, lighter on a dark one."""
    if contrast(fg, bg) >= target:
        return fg
    toward = (0, 0, 0) if lum(bg) > 0.18 else (255, 255, 255)
    for step in range(1, 101):
        t = step / 100
        c = tuple(round(fg[i] + (toward[i] - fg[i]) * t) for i in range(3)) + (1.0,)
        if contrast(c, bg) >= target:
            return c
    return toward + (1.0,)


# ------------------------------------------------------------------ sizes
def px(v):
    m = re.match(r"^(-?[\d.]+)px$", v.strip())
    return float(m.group(1)) if m else None


def to_pt(px_value, scale=1.0):
    """CSS px to Power Apps points at the app's scale, to the nearest half point."""
    return round(px_value * scale * 0.75 * 2) / 2


def text_h(pt, line_height=1.3, lines=1, pad=0):
    """The height a label needs for `lines` lines of text at `pt` points (its PaddingTop + PaddingBottom given as pad)."""
    return int(math.ceil(pt / 0.75 * line_height * lines)) + pad


def font_size(decls):
    """(px, line-height, weight) from font-size / line-height / font-weight or the font shorthand."""
    size = px(decls.get("font-size", "")) if "font-size" in decls else None
    lh = decls.get("line-height")
    weight = decls.get("font-weight")
    f = decls.get("font")
    if f:
        m = re.search(r"(?:(\d{3}|bold|normal)\s+)?(\d+(?:\.\d+)?)px(?:\s*/\s*([\d.]+(?:px)?))?", f)
        if m:
            weight = weight or m.group(1)
            size = size or float(m.group(2))
            lh = lh or m.group(3)
    if lh and lh.endswith("px") and size:
        lh = str(round(float(lh[:-2]) / size, 3))
    return size, (float(lh) if lh and re.fullmatch(r"[\d.]+", lh) else None), weight


def first_font(stack):
    for f in [s.strip().strip("'\"") for s in stack.split(",")]:
        if f.lower() in SYSTEM_FONTS:
            return "Segoe UI", f
        for pa in PA_FONTS:
            if f.lower() == pa.lower():
                return pa, f
    return "Segoe UI", None


# ------------------------------------------------------------------ the whole design
def token_name(var):
    for pat, tok in TOKEN_RULES:
        if re.search(pat, var):
            return re.sub(pat, tok, var) if "\\1" in tok else tok
    return None


def extract(html, content_w, proto_content_w=None):
    rules = parse_css(css_of(html))
    light, dark = custom_properties(rules)
    if proto_content_w is None:
        widths = [px(r["decls"]["max-width"]) for r in rules if not r["media"] and px(r["decls"].get("max-width", "") or "")]
        proto_content_w = max(widths) if widths else content_w
    scale = content_w / proto_content_w
    base_light = color(resolve(light.get("base", light.get("bg", light.get("background", "#ffffff"))), light)) or (255, 255, 255, 1.0)
    base_dark = color(resolve(dark.get("base", dark.get("bg", dark.get("background", ""))), dark, light)) if dark else None

    tokens = {}
    for var in light:
        name = token_name(var)
        if not name:
            continue
        lc = color(resolve(light[var], light))
        dc = color(resolve(dark[var], dark, light)) if var in dark else None
        if lc is None:
            continue
        tokens[name] = {"css": f"--{var}", "light": lc, "dark": dc}

    def solid(name, scheme):
        t = tokens.get(name)
        base = base_light if scheme == "light" else (base_dark or base_light)
        c = t and t.get(scheme)
        if not c:
            return base
        surf = tokens.get("ColorSurface", {}).get(scheme)
        over = composite(surf, base) if (surf and name not in ("ColorBackground", "ColorSurface")) else base
        return composite(c, over)

    checks = []
    for fg, bg in TEXT_ON.items():
        if fg not in tokens:
            continue
        for scheme in ("light", "dark"):
            if scheme == "dark" and not tokens[fg]["dark"]:
                continue
            f, b = solid(fg, scheme), solid(bg, scheme)
            r = contrast(f, b)
            fix = compliant(f, b)
            checks.append({"token": fg, "on": bg, "scheme": scheme, "fg": hexs(f), "bg": hexs(b), "ratio": r, "pass": r >= 4.5,
                           "compliant": hexs(fix) if r < 4.5 else None, "compliant_ratio": contrast(fix, b) if r < 4.5 else None})
    on_primary = None
    if "ColorPrimary" in tokens:
        p = solid("ColorPrimary", "light")
        on_primary = {"white_on_primary": contrast((255, 255, 255, 1), p), "compliant_primary": hexs(compliant(p, (255, 255, 255, 1)))}

    type_scale, geometry, shadows, gradients, fonts = [], [], [], [], []
    for r in rules:
        d = {k: resolve(v, light) for k, v in r["decls"].items()}
        size, lh, weight = font_size(d)
        if size:
            pt = to_pt(size, scale)
            type_scale.append({"selector": r["selector"], "media": r["media"], "px": size, "pt": pt, "weight": weight,
                               "line_height": lh, "label_h": text_h(pt, lh or 1.3)})
        g = {}
        for prop in ("border-radius", "padding", "gap", "height", "min-height", "width", "max-width", "margin"):
            if prop in d:
                vals = [px(x) for x in d[prop].split()]
                if any(v is not None for v in vals):
                    g[prop] = [round(v * scale) if v is not None else None for v in vals]
        if g:
            geometry.append({"selector": r["selector"], "media": r["media"], **g})
        if "box-shadow" in d:
            shadows.append({"selector": r["selector"], "value": d["box-shadow"]})
        for prop in ("background", "background-image"):
            if "gradient(" in d.get(prop, ""):
                gradients.append({"selector": r["selector"], "media": r["media"], "value": d[prop]})
        for prop in ("font", "font-family"):
            if prop == "font-family" or (prop in d and "," in d.get(prop, "")):
                stack = d.get("font-family") or re.sub(r"^.*?px(?:/[\d.]+)?\s+", "", d.get("font", ""))
                if stack and "," in stack:
                    pa, matched = first_font(stack)
                    fonts.append({"selector": r["selector"], "stack": stack, "power_apps": pa, "matched": matched})
                break
    return {"scale": round(scale, 4), "content_width": content_w, "prototype_content_width": proto_content_w,
            "has_dark_scheme": bool(dark), "custom_properties": {"light": light, "dark": dark},
            "tokens": {k: {"css": v["css"], "light": rgba_fx(v["light"]), "light_hex": hexs(composite(v["light"], base_light)),
                           "dark": rgba_fx(v["dark"]) if v["dark"] else None,
                           "dark_hex": hexs(composite(v["dark"], base_dark or base_light)) if v["dark"] else None}
                       for k, v in tokens.items()},
            "contrast": checks, "on_primary": on_primary, "type_scale": type_scale, "geometry": geometry, "shadows": shadows,
            "gradients": gradients, "fonts": fonts}


def formulas(design):
    """App.Formulas lines: each token light or dark by IsDark, plus a Hex<Token> text for SVG images. A proposal for /design-spec."""
    out = ['IsDark = Coalesce(First(colScheme).Value, "Light") = "Dark";']
    for name, t in design["tokens"].items():
        light, dark = t["light"], t["dark"] or t["light"]
        out.append(f"{name} = {light};" if light == dark else f"{name} = If(IsDark, {dark}, {light});")
    for name, t in design["tokens"].items():
        lh, dh = t["light_hex"], t["dark_hex"] or t["light_hex"]
        out.append(f'Hex{name[5:]} = "{lh}";' if lh == dh else f'Hex{name[5:]} = If(IsDark, "{dh}", "{lh}");')
    return out


def check_app(design, app_yaml_text):
    """Compare App.Formulas with the measured design. Errors: a measured colour with no token, or no IsDark when the prototype has a dark
    scheme. Warnings: a token whose value differs from the prototype's (allowed only as a compliant variant recorded in design-spec section 8)."""
    defs = {m.group(1): re.sub(r"\s+", " ", m.group(2).strip()) for m in re.finditer(r"^\s*=?\s*(\w+)\s*=\s*(.+?);\s*(?://.*)?$", app_yaml_text, re.M)}
    errors, warnings = [], []
    if design["has_dark_scheme"] and "IsDark" not in defs:
        errors.append("the prototype has a dark scheme but App.Formulas defines no IsDark (design-standards section 3)")
    for name, t in design["tokens"].items():
        if name not in defs:
            errors.append(f"{name} ({t['css']}) is measured in the prototype but not defined in App.Formulas")
            continue
        light, dark = t["light"], t["dark"]
        want = f"If(IsDark, {dark}, {light})" if dark and dark != light and design["has_dark_scheme"] else light
        if defs[name] != want:
            warnings.append(f"{name} = {defs[name]}; the prototype gives {want} (fine only as a compliant variant in design-spec section 8)")
    return errors, warnings


def report(d):
    lines = [f"scale {d['scale']} (app content {d['content_width']} / prototype content {d['prototype_content_width']}); dark scheme: {d['has_dark_scheme']}", "",
             "TOKENS (proposal)"]
    for k, t in d["tokens"].items():
        lines.append(f"  {k:22} {t['css']:12} light {t['light']:28} dark {t['dark'] or '-'}")
    lines += ["", "CONTRAST (text on its surface)"]
    for c in d["contrast"]:
        lines.append(f"  {c['scheme']:5} {c['token']:18} on {c['on']:18} {c['ratio']:5}:1 {'ok' if c['pass'] else 'FAIL -> ' + c['compliant'] + ' (' + str(c['compliant_ratio']) + ':1)'}")
    if d["on_primary"]:
        lines.append(f"  white on primary {d['on_primary']['white_on_primary']}:1 (compliant primary {d['on_primary']['compliant_primary']})")
    lines += ["", "TYPE SCALE (px -> pt at the app's scale, label height)"]
    for t in d["type_scale"]:
        lines.append(f"  {t['selector'][:34]:34} {t['px']:5}px -> {t['pt']:5}pt  h {t['label_h']:3}  weight {t['weight'] or '-'}" + (f"  [{t['media']}]" if t['media'] else ""))
    lines += ["", "GEOMETRY (scaled px)"]
    for g in d["geometry"]:
        lines.append(f"  {g['selector'][:34]:34} " + "  ".join(f"{k} {v}" for k, v in g.items() if k not in ("selector", "media")))
    lines += ["", "SHADOWS"] + [f"  {s['selector'][:34]:34} {s['value']}" for s in d["shadows"]]
    lines += ["", "GRADIENTS"] + [f"  {g['selector'][:34]:34} {g['value'][:110]}" for g in d["gradients"]]
    lines += ["", "FONTS"] + [f"  {f['selector'][:34]:34} -> Font.'{f['power_apps']}' (matched {f['matched']})" for f in d["fonts"]]
    return "\n".join(lines)


SELFTEST_HTML = """<style>
:root{--text:#1d1d1f;--muted:#8e8e93;--blue:#007aff;--base:#eef0f6;--glass:rgba(255,255,255,.58);--glass2:rgba(255,255,255,.82)}
@media(prefers-color-scheme:dark){:root{--text:#f5f5f7;--muted:#a1a1a6;--blue:#0a84ff;--base:#0b0b10}}
body{font:15px/1.47 -apple-system,"Segoe UI",sans-serif;background:var(--base)}
main{max-width:1060px}
.card{border-radius:24px;padding:20px 22px;box-shadow:0 10px 40px rgba(0,0,0,.1)}
.card h3{font-size:19px;font-weight:600}
body::before{background:radial-gradient(55% 50% at 12% 8%,#cfe3ff,transparent 70%)}
</style>"""


def selftest():
    d = extract(SELFTEST_HTML, 1020)
    assert d["prototype_content_width"] == 1060 and d["has_dark_scheme"], d["prototype_content_width"]
    assert d["tokens"]["ColorText"]["light"] == "RGBA(29, 29, 31, 1)" and d["tokens"]["ColorText"]["dark"] == "RGBA(245, 245, 247, 1)"
    assert d["tokens"]["ColorGlass"]["light"] == "RGBA(255, 255, 255, 0.58)"
    muted = [c for c in d["contrast"] if c["token"] == "ColorTextMuted" and c["scheme"] == "light"][0]
    assert not muted["pass"] and contrast(color(muted["compliant"]), color(muted["bg"])) >= 4.5
    body = [t for t in d["type_scale"] if t["selector"] == "body"][0]
    assert body["px"] == 15 and body["pt"] == 11 and body["line_height"] == 1.47, body
    h3 = [t for t in d["type_scale"] if t["selector"] == ".card h3"][0]
    assert h3["pt"] == 13.5 and h3["weight"] == "600", h3
    card = [g for g in d["geometry"] if g["selector"] == ".card"][0]
    assert card["border-radius"] == [23] and card["padding"] == [19, 21], card
    assert d["fonts"][0]["power_apps"] == "Segoe UI" and d["gradients"]
    f = formulas(d)
    assert 'ColorText = If(IsDark, RGBA(245, 245, 247, 1), RGBA(29, 29, 31, 1));' in f, f
    assert any(x.startswith("HexPrimary = If(IsDark,") for x in f)
    assert to_pt(32, 1.0) == 24 and text_h(11, 1.47) == 22
    # a hand-written prototype: short names, and a dark scheme switched by data-theme (not the device)
    d2 = extract("<style>:root{--bg:#f6f7f9;--c:#fff;--tx:#101828;--mu:#667085;--ac:#4f46e5;--bd:#e4e7ec}"
                 "[data-theme=dark]{color-scheme:dark;--bg:#0b0f17;--c:#121826;--tx:#e6e9ef;--ac:#818cf8}body{font:14px/1.5 Inter}</style>", 1020)
    assert d2["has_dark_scheme"], "data-theme dark block not seen"
    assert d2["tokens"]["ColorPrimary"]["light"] == "RGBA(79, 70, 229, 1)" and d2["tokens"]["ColorPrimary"]["dark"] == "RGBA(129, 140, 248, 1)", d2["tokens"].get("ColorPrimary")
    assert d2["tokens"]["ColorSurface"]["dark"] == "RGBA(18, 24, 38, 1)" and d2["tokens"]["ColorDivider"]["light"] == "RGBA(228, 231, 236, 1)"
    print("prototype_design self-test: OK")


def main(argv):
    if "--selftest" in argv:
        selftest()
        return 0
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 1
    content = int(argv[argv.index("--content") + 1]) if "--content" in argv else 1020
    proto = int(argv[argv.index("--prototype-width") + 1]) if "--prototype-width" in argv else None
    d = extract(Path(argv[0]).read_text(encoding="utf-8"), content, proto)
    if "--check" in argv:
        errors, warnings = check_app(d, Path(argv[argv.index("--check") + 1]).read_text(encoding="utf-8"))
        for w in warnings:
            print("  WARN ", w)
        for e in errors:
            print("  FAIL ", e)
        print(f"  -> {len(errors)} error(s), {len(warnings)} warning(s): App.Formulas against the prototype's measured design")
        return 1 if errors else 0
    if "--out" in argv:
        out = Path(argv[argv.index("--out") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(d, indent=1), encoding="utf-8")
    print(report(d))
    if "--formulas" in argv:
        print("\nAPP.FORMULAS (proposal)")
        print("\n".join("      " + x for x in formulas(d)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
