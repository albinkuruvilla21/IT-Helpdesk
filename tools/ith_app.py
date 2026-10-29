"""ith_app: the IT Help project's design tokens (specs/design-spec.md section 2). Project-specific; the generic builders are canvas_ui.py.

    uv run tools/ith_app.py tokens      rewrite the token block of canvas/ITHelp/Src/App.pa.yaml (stage G3), keeping the rest of the file

Derived from inputs/design/index (4).html (no brand guide), light and dark schemes (the prototype switches with data-theme="dark").
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canvas_ui import tokens_block  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "canvas" / "ITHelp" / "Src" / "App.pa.yaml"


def rgba(h, a=1):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"RGBA({r}, {g}, {b}, {a})"


# token: (light hex, dark hex, alpha light, alpha dark). A compliant variant is marked in specs/design-spec.md section 8.
PALETTE = {
    "ColorPrimary": ("#4f46e5", "#4f46e5"),            # --ac, .btn.p fill (the dark scheme keeps #4f46e5 for buttons)
    "ColorPrimaryHover": ("#4338ca", "#4338ca"),       # --ah
    "ColorPrimaryPressed": ("#3730a3", "#3730a3"),     # derived: primary mixed with black
    "ColorOnPrimary": ("#ffffff", "#ffffff"),
    "ColorSecondary": ("#101828", "#e6e9ef"),          # unused by this app; kept equal to ColorText
    "ColorOnSecondary": ("#ffffff", "#101828"),
    "ColorText": ("#101828", "#e6e9ef"),               # --tx
    "ColorTextMuted": ("#667085", "#98a2b3"),          # --mu
    "ColorBorder": ("#838a98", "#657084"),             # control outline, compliant variant of --bd (3:1), design-spec section 8
    "ColorDivider": ("#e4e7ec", "#263041"),            # --bd: card and bar borders, decorative
    "ColorBackground": ("#f6f7f9", "#0b0f17"),         # --bg
    "ColorSurface": ("#ffffff", "#121826"),            # --c
    "ColorSuccessFill": ("#deede4", "#223639"),
    "ColorWarningFill": ("#f4e7dd", "#33322b"),
    "ColorErrorFill": ("#f5dfdf", "#332c38"),
    "ColorInfoFill": ("#dfe6fa", "#243044"),
    "ColorNeutralFill": ("#e5e7ea", "#2c3240"),
    "ColorError": ("#b91c1c", "#fca5a5"),              # Critical, danger and error text
    # added tokens: each is needed by a prototype element (design-spec section 2)
    "ColorPrimaryTint": ("#eef2ff", "#1e2347"),        # --as: current nav item, avatar, chip on
    "ColorPrimaryTintBorder": ("#c7d2fe", "#c7d2fe"),  # .chip.on and .kb .card:hover border
    "ColorAccentText": ("#4f46e5", "#818cf8"),         # --ac as text: ticket IDs, current nav text, links
    "ColorSunken": ("#fcfcfd", "#151b29"),             # --h3: table head
    "ColorHover": ("#f2f4f7", "#1b2335"),              # --h: hover, progress track, count pill
    "ColorRowHover": ("#f9fafb", "#161d2c"),           # --h2: row hover
    "ColorLine": ("#f0f2f5", "#1c2434"),               # --ln: row separator
    "ColorDot": ("#dc2626", "#dc2626"),                # .dot: unread notifications
    "ColorSuccess": ("#147839", "#86efac"),            # Resolved (compliant variant of #15803d)
    "ColorWarning": ("#a94e08", "#fcd34d"),            # In Progress (compliant variant of #b45309)
    "ColorInfo": ("#1d4ed8", "#93c5fd"),               # Open, Medium
    "ColorNeutralText": ("#475467", "#cbd5e1"),        # On Hold, Low
    "ColorClosed": ("#616a7e", "#94a3b8"),             # Closed (compliant variant of #667085)
    "ColorClosedFill": ("#eaebee", "#242b3a"),
    "ColorHigh": ("#ba3e0c", "#fdba74"),               # High (compliant variant of #c2410c)
    "ColorHighFill": ("#f6e4dd", "#332f31"),
}
ALPHA = {"ColorOverlay": (rgba("#101828", 0.4), rgba("#000000", 0.67))}

# Hex texts for SVG images (logo tile, nav icons, progress bars): same values as the tokens
HEX_KEYS = ["ColorPrimary", "ColorAccentText", "ColorText", "ColorTextMuted", "ColorSurface", "ColorDivider", "ColorPrimaryTint", "ColorHover",
            "ColorInfo", "ColorWarning", "ColorNeutralText", "ColorSuccess", "ColorClosed", "ColorHigh", "ColorError", "ColorOnPrimary"]

HEADER = ("      =// Design tokens. The client's brand lives here and only here: screens use these names, never RGBA literals (D11).\n"
          "      // Derived from the accepted prototype (no brand guide), light and dark schemes: specs/design-spec.md section 2 (AC-ITH-09.1). Never rename a token.\n")


def overrides_and_dark():
    over, dark = {}, {}
    for k, (lh, dh) in PALETTE.items():
        over[k] = rgba(lh)
        dark[k] = rgba(dh)
    for k, (lv, dv) in ALPHA.items():
        over[k], dark[k] = lv, dv
    return over, dark


def hexes():
    return {k: (PALETTE[k][0], PALETTE[k][1]) for k in HEX_KEYS}


def tokens_text():
    over, dark = overrides_and_dark()
    return HEADER + tokens_block(over, dark=dark, hexes=hexes())


def rewrite_tokens():
    """Replace the token lines of App.Formulas (everything from the first `=` line up to AppTitle), keeping AppTitle and the rest of the file."""
    text = APP.read_text(encoding="utf-8")
    m = re.search(r"(    Formulas: \|-\n)(.*?)(      AppTitle = )", text, re.S)
    assert m, "App.pa.yaml has no Formulas block ending in AppTitle"
    APP.write_text(text[:m.start(2)] + tokens_text() + text[m.start(3):], encoding="utf-8")
    print("tokens written to", APP)


if __name__ == "__main__":
    if sys.argv[1:] == ["tokens"]:
        rewrite_tokens()
    else:
        print(__doc__)
