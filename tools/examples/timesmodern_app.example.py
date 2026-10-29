"""mt_app: the TimesModern project's tokens and App.pa.yaml (specs/design-spec.md section 2). Project-specific; the generic builders are canvas_ui.py.

    uv run tools/mt_app.py tokens      rewrite the token block of canvas/TimesModern/Src/App.pa.yaml (stage G3), keeping the rest of the file
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canvas_ui import tokens_block  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "canvas" / "TimesModern" / "Src" / "App.pa.yaml"

# design-spec section 2: light scheme only (the prototype defines no dark scheme)
OVERRIDES = {
    "ColorPrimary": "RGBA(79, 70, 229, 1)", "ColorPrimaryHover": "RGBA(67, 56, 202, 1)", "ColorPrimaryPressed": "RGBA(55, 48, 163, 1)",
    "ColorOnPrimary": "RGBA(255, 255, 255, 1)", "ColorSecondary": "RGBA(28, 32, 48, 1)", "ColorOnSecondary": "RGBA(255, 255, 255, 1)",
    "ColorOnSecondaryMuted": "RGBA(255, 255, 255, 0.8)", "ColorText": "RGBA(28, 32, 48, 1)", "ColorTextMuted": "RGBA(106, 113, 127, 1)",
    "ColorBorder": "RGBA(134, 139, 153, 1)", "ColorDivider": "RGBA(231, 233, 238, 1)", "ColorBackground": "RGBA(245, 246, 248, 1)",
    "ColorSurface": "RGBA(255, 255, 255, 1)", "ColorOverlay": "RGBA(17, 24, 39, 0.4)",
    "ColorSuccessFill": "RGBA(232, 246, 238, 1)", "ColorWarningFill": "RGBA(253, 243, 225, 1)", "ColorErrorFill": "RGBA(253, 234, 234, 1)",
    "ColorInfoFill": "RGBA(238, 240, 255, 1)", "ColorNeutralFill": "RGBA(239, 240, 243, 1)",
    "ColorError": "RGBA(185, 28, 28, 1)", "ColorErrorHover": "RGBA(153, 22, 22, 1)", "ColorErrorPressed": "RGBA(127, 29, 29, 1)",
    # added tokens: each is needed by a prototype element (design-spec section 2)
    "ColorPrimaryTint": "RGBA(238, 240, 255, 1)",   # --accent-soft: active nav item, avatar, Active and In progress badge
    "ColorSunken": "RGBA(250, 251, 252, 1)",        # th background: table header row
    "ColorSuccess": "RGBA(21, 128, 61, 1)",         # --green: Completed and Done badge text
    "ColorWarning": "RGBA(180, 83, 9, 1)",          # --amber: On hold and Medium badge text
    "ColorNeutralText": "RGBA(95, 102, 115, 1)",    # --muted on gray-soft, compliant variant: Planning, To do, Low badge text
}

# Hex texts for SVG images (logo tile, nav icons, progress bars): same values as the tokens
HEXES = {"ColorPrimary": ("#4f46e5", None), "ColorPrimaryTint": ("#eef0ff", None), "ColorText": ("#1c2030", None),
         "ColorTextMuted": ("#6a717f", None), "ColorSurface": ("#ffffff", None), "ColorBackground": ("#f5f6f8", None),
         "ColorDivider": ("#e7e9ee", None), "ColorNeutralFill": ("#eff0f3", None), "ColorOnPrimary": ("#ffffff", None)}

HEADER = ("      =// Design tokens. The client's brand lives here and only here: screens use these names, never RGBA literals (D11).\n"
          "      // Derived from the accepted prototype (no brand guide), light scheme only (AC-NAV-03.2): specs/design-spec.md section 2. Never rename a token.\n")


def tokens_text():
    return HEADER + tokens_block(OVERRIDES, hexes=HEXES)


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
