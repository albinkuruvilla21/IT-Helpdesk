"""canvas_ui: build Power Apps canvas screens (.pa.yaml) from the layout patterns of the reference app.

WHY THIS EXISTS. Screens generated from computed sizes, nested flexible auto-layout and container badges built and
passed `pp.py build`, then laid out badly in Studio (clipped text, overflowing inputs, cut-off buttons). A hand-built
Studio app (samples/powerapp) laid out correctly. This module encodes ITS patterns, number for number: header and
navigation placed on the screen, ONE scrolling auto-layout body, sections with explicit heights, tables as a gallery
inside a fixed-height ManualLayout wrapper, ModernText badges, segmented buttons, dialogs as absolutely positioned
controls over an overlay. Read docs/standards/ui-patterns.md first; never invent a layout.

RULES THIS MODULE ENFORCES
  * Colours are design tokens only (App.Formulas); sizes are the plain numbers below (CLAUDE.md D11).
  * Control names are unique on a screen (PA2110).
  * `LayoutMode` is never set on a container and `Layout` never on a gallery (PA2108, PA-T21).
  * A comment added to a formula is part of the formula, so it stays inside any quotes (PA1001).

USE
    import sys; sys.path.insert(0, "tools")
    from canvas_ui import *
    s = Screen("scrDocuments", "doc", active_tab=1, on_visible="Set(varLoading, false)")
    s.body = [title("docTitle", "Documents"), ...]
    s.write("canvas/MyApp/Src")

    uv run tools/canvas_ui.py --selftest    rebuilds parts of samples/powerapp with this module and compares them with the sample
"""
import re
import sys
from pathlib import Path

NL = chr(10)

# ------------------------------------------------------------------ the numbers (from samples/powerapp; do not tune)
HEADER_H, TITLE_H, SUB_H, NAV_H = 56, 28, 18, 44
TAB_W, TAB_H, TAB_X, TAB_Y, TAB_STEP, LINE_H, LINE_Y = 130, 36, 20, 60, 136, 3, 96
BODY_Y, BODY_GAP, PAD_TOP, PAD_BOTTOM, CONTENT_W = 100, 12, 16, 24, 1150
CARD_H, CARD_GAP, FIELD_H, FIELD_ROW_H, CTRL_H, BTN_H, SMALL_BTN_H = 70, 10, 56, 62, 34, 36, 28
TABLE_HEAD_H, ROW_H, SUBROW_H, FORM_ROW_H, SEP_H = 30, 46, 34, 40, 1
MODAL_W, MODAL_Y, MODAL_PAD = 560, 110, 20

# Colour tokens every project defines in App.Formulas. The brand values replace the defaults; the NAMES are fixed.
TOKENS = {
    "ColorPrimary": "RGBA(15, 108, 189, 1)", "ColorPrimaryHover": "RGBA(16, 94, 165, 1)", "ColorPrimaryPressed": "RGBA(12, 76, 134, 1)",
    "ColorOnPrimary": "RGBA(255, 255, 255, 1)", "ColorSecondary": "RGBA(15, 42, 74, 1)", "ColorOnSecondary": "RGBA(255, 255, 255, 1)",
    "ColorOnSecondaryMuted": "RGBA(255, 255, 255, 0.8)", "ColorText": "RGBA(32, 31, 30, 1)", "ColorTextMuted": "RGBA(96, 94, 92, 1)",
    "ColorBorder": "RGBA(138, 136, 134, 1)", "ColorDivider": "RGBA(210, 208, 206, 1)", "ColorBackground": "RGBA(255, 255, 255, 1)",
    "ColorSurface": "RGBA(243, 242, 241, 1)", "ColorDisabled": "RGBA(161, 159, 157, 1)", "ColorTransparent": "RGBA(0, 0, 0, 0)",
    "ColorHoverOverlay": "RGBA(0, 0, 0, 0.06)", "ColorPressedOverlay": "RGBA(0, 0, 0, 0.12)", "ColorOverlay": "RGBA(0, 0, 0, 0.45)",
    "ColorSuccessFill": "RGBA(199, 233, 192, 1)", "ColorWarningFill": "RGBA(254, 217, 168, 1)", "ColorErrorFill": "RGBA(244, 182, 182, 1)",
    "ColorInfoFill": "RGBA(188, 215, 242, 1)", "ColorNeutralFill": "RGBA(221, 221, 221, 1)", "ColorError": "RGBA(196, 49, 75, 1)",
    "ColorErrorHover": "RGBA(170, 40, 62, 1)", "ColorErrorPressed": "RGBA(140, 30, 50, 1)", "ColorNoteFill": "RGBA(255, 244, 206, 1)",
    "ColorNoteBorder": "RGBA(232, 201, 90, 1)", "FontBody": "Font.'Segoe UI'",
}


def tokens_block(overrides=None, dark=None, hexes=None):
    """The token lines for App.Formulas (6-space indent). `overrides` replaces values; names never change.
    dark: {token: RGBA(...)} for the prototype's dark scheme; each such token becomes If(IsDark, dark, light) and IsDark is defined from colScheme.
    hexes: {token: (light_hex, dark_hex_or_None)}: Hex<Name> texts for SVG images (svg_ring, svg_backdrop, svg_tile). Values come from
    tools/prototype_design.py and design-spec section 2."""
    t = {**TOKENS, **(overrides or {})}
    lines = []
    if dark:
        lines.append('      IsDark = Coalesce(First(colScheme).Value, "Light") = "Dark";')
    for k, v in t.items():
        lines.append(f"      {k} = If(IsDark, {dark[k]}, {v});" if dark and k in dark and dark[k] != v else f"      {k} = {v};")
    for k, (lh, dh) in (hexes or {}).items():
        name = "Hex" + (k[5:] if k.startswith("Color") else k)
        lines.append(f'      {name} = If(IsDark, "{dh}", "{lh}");' if dh and dh != lh else f'      {name} = "{lh}";')
    return NL.join(lines) + NL


# ------------------------------------------------------------------ nodes and YAML
class Node:
    def __init__(self, name, control, props, children=None, variant=None):
        self.name, self.control, self.props, self.children, self.variant = name, control, props, children or [], variant


def _eq(v):
    v = str(v)
    return v if v.startswith("=") else "=" + v


def _q(v):
    assert " #" not in v, f"' #' in a plain value breaks YAML: {v[:60]}"
    if ": " in v or v.endswith(":"):
        return "'" + v.replace("'", "''") + "'"
    return v


def _with_comment(value, ac):
    """Append `// ac` to a formula as a comment. Quoting is applied afterwards (_q), so the comment is always inside the quotes."""
    return value if (not ac or "//" in str(value)) else f"{value} // {ac}"


def emit(n, ind):
    pad = " " * ind
    out = [f"{pad}- {n.name}:", f"{pad}    Control: {n.control}"]
    if n.variant:
        out.append(f"{pad}    Variant: {n.variant}")
    out.append(f"{pad}    Properties:")
    for k, v in n.props.items():
        v = _eq(v)
        if NL in v:
            out.append(f"{pad}      {k}: |-")
            out.extend(f"{pad}        {ln}" if ln.strip() else "" for ln in v.split(NL))
        else:
            out.append(f"{pad}      {k}: {_q(v)}")
    if n.children:
        out.append(f"{pad}    Children:")
        for c in n.children:
            out.extend(emit(c, ind + 6))
    return out


def _walk(nodes):
    for n in nodes:
        yield n
        yield from _walk(n.children)


def _txt(text):
    """A literal string, or a formula when it starts with '='."""
    return text if str(text).startswith("=") else f'"{text}"'


# ------------------------------------------------------------------ controls
def label(name, text, size=12, bold=False, color="ColorText", h=None, w=None, x=None, y=None, fill=None, align=None, valign=None,
          visible=None, fp=None, pad_left=None, border=None, align_in=None, ac=None, role=None):
    p = {"Color": color, "Font": "FontBody"}
    if bold:
        p["FontWeight"] = "FontWeight.Semibold"
    if h is not None:
        p["Height"] = h
    p["Size"] = size
    p["Text"] = _with_comment(_txt(text), ac)
    for k, v in (("Width", w), ("X", x), ("Y", y), ("Fill", fill), ("Visible", visible), ("FillPortions", fp), ("PaddingLeft", pad_left),
                 ("AlignInContainer", align_in)):
        if v is not None:
            p[k] = v
    if align:
        p["Align"] = f"Align.{align}"
    if valign:
        p["VerticalAlign"] = f"VerticalAlign.{valign}"
    if border:
        p["BorderColor"], p["BorderThickness"] = border, 1
    if role:
        p["Role"] = f"TextRole.{role}"  # Heading1 / Heading2: a screen reader announces it as a heading
    return Node(name, "Label@2.5.1", p)


_BTN = {  # border, fill, text, hover fill, pressed fill, hover text
    "secondary": ("ColorBorder", "ColorBackground", "ColorText", "ColorSurface", "ColorDivider", "ColorText"),
    "primary": ("ColorPrimary", "ColorPrimary", "ColorOnPrimary", "ColorPrimaryHover", "ColorPrimaryPressed", "ColorOnPrimary"),
    "danger": ("ColorError", "ColorError", "ColorOnPrimary", "ColorErrorHover", "ColorErrorPressed", "ColorOnPrimary"),
    "tab": ("ColorTransparent", "ColorTransparent", "ColorText", "ColorHoverOverlay", "ColorPressedOverlay", "ColorText"),
}


def button(name, text, onselect, kind="secondary", w=None, h=BTN_H, x=None, y=None, visible=None, fp=None, fill=None, color=None,
           hover_fill=None, pressed_fill=None, bold=False, size=12, align_in=None, display=None, ac=None, weight=None, radius=None):
    bd, fl, tx, hv, pr, htx = _BTN[kind]
    p = {}
    if align_in:
        p["AlignInContainer"] = align_in
    p.update({"BorderColor": bd, "BorderThickness": 1, "Color": color or tx, "DisabledBorderColor": "ColorDivider", "DisabledColor": "ColorDisabled",
              "DisabledFill": "ColorSurface", "Fill": fill or fl, "Font": "FontBody"})
    if bold:
        p["FontWeight"] = "FontWeight.Semibold"
    elif weight:
        p["FontWeight"] = weight
    p.update({"Height": h, "HoverBorderColor": bd, "HoverColor": htx, "HoverFill": hover_fill or hv, "OnSelect": _with_comment(onselect, ac),
              "PressedBorderColor": bd, "PressedColor": htx, "PressedFill": pressed_fill or pr, "RadiusBottomLeft": 2, "RadiusBottomRight": 2,
              "RadiusTopLeft": 2, "RadiusTopRight": 2, "Size": size, "Text": _txt(text)})
    for k, v in (("Width", w), ("X", x), ("Y", y), ("Visible", visible), ("FillPortions", fp), ("DisplayMode", display)):
        if v is not None:
            p[k] = v
    if radius is not None:  # "pill" = half the height, as a prototype's border-radius: 999px
        for k in ("RadiusTopLeft", "RadiusTopRight", "RadiusBottomLeft", "RadiusBottomRight"):
            p[k] = h // 2 if radius == "pill" and isinstance(h, int) else radius
    return Node(name, "Classic/Button@2.2.0", p)


def textinput(name, default='""', hint="", h=CTRL_H, multiline=False, fp=None, w=None, x=None, y=None, visible=None, display=None,
              onchange=None, align_in=None, accessible=None, ac=None):
    p = {}
    if accessible:
        p["AccessibleLabel"] = _txt(accessible)
    if align_in:
        p["AlignInContainer"] = align_in
    p.update({"BorderColor": "ColorBorder", "BorderThickness": 1, "Color": "ColorText", "Default": _with_comment(default, ac), "Height": h,
              "HintText": f'"{hint}"', "PaddingLeft": 8, "RadiusBottomLeft": 2, "RadiusBottomRight": 2, "RadiusTopLeft": 2, "RadiusTopRight": 2, "Size": 12})
    if multiline:
        p["Mode"] = "TextMode.MultiLine"
    for k, v in (("FillPortions", fp), ("Width", w), ("X", x), ("Y", y), ("Visible", visible), ("DisplayMode", display), ("OnChange", onchange)):
        if v is not None:
            p[k] = v
    return Node(name, "Classic/TextInput@2.3.2", p)


def dropdown(name, items, ac=None):
    """ModernDropdown over a one-column collection {Value}; read it with Coalesce(<name>.Selected.Value, "All")."""
    return Node(name, "ModernDropdown@1.0.3", {"Height": CTRL_H, "ItemDisplayText": "ThisItem.Value", "Items": _with_comment(items, ac),
                                              "LayoutMinHeight": 16, "LayoutMinWidth": 16})


def badge(name, status_expr, fill_switch, fp=None, w=None, h=30, radius=12, size=11):
    """A status pill: ModernText with a rounded fill. fill_switch is a Switch(...) over tokens; the status is always written in words."""
    p = {"Align": "Align.Center", "AlignInContainer": "AlignInContainer.Center", "Color": "ColorText", "Fill": fill_switch}
    if fp is not None:
        p["FillPortions"] = fp
    p.update({"FontWeight": "FontWeight.Semibold", "Height": h, "LayoutMinHeight": 16, "LayoutMinWidth": 16, "RadiusBottomLeft": radius, "RadiusBottomRight": radius,
              "RadiusTopLeft": radius, "RadiusTopRight": radius, "Size": size, "Text": status_expr})
    if w is not None:
        p["Width"] = w
    return Node(name, "ModernText@1.0.0", p)


def rect(name, fill, h, w=None, x=None, y=None, visible=None, border="ColorTransparent"):
    p = {"BorderColor": border, "Fill": fill, "Height": h}
    for k, v in (("Width", w), ("X", x), ("Y", y), ("Visible", visible)):
        if v is not None:
            p[k] = v
    return Node(name, "Rectangle@2.3.0", p)


def box(name, children, direction="Vertical", gap=0, h=None, w=None, y=None, fill=None, pad=None, pad_x=None, pad_y=None, border=False, fp=None,
        visible=None, align="Stretch", scroll=False, shadow="None", min0=True, radius=None, border_color="ColorDivider"):
    """An auto-layout container with the sample's property set. `fp=0` for a fixed-height child of a vertical container.
    radius: the prototype's border-radius (scaled); border_color: the prototype's border token (ColorGlassStroke on glass cards)."""
    p = {"DropShadow": f"DropShadow.{shadow}"}
    if border:
        p["BorderColor"], p["BorderThickness"] = border_color, 1
    if radius is not None:
        for k in ("RadiusTopLeft", "RadiusTopRight", "RadiusBottomLeft", "RadiusBottomRight"):
            p[k] = radius
    if fill:
        p["Fill"] = fill
    if fp is not None:
        p["FillPortions"] = fp
    if h is not None:
        p["Height"] = h
    p.update({"LayoutAlignItems": f"LayoutAlignItems.{align}", "LayoutDirection": f"LayoutDirection.{direction}"})
    if gap is not None:
        p["LayoutGap"] = gap
    if scroll:
        p["LayoutOverflowY"] = "LayoutOverflow.Scroll"
    if min0:
        p["LayoutMinHeight"], p["LayoutMinWidth"] = 0, 0
    sides = {"Bottom": pad, "Left": pad, "Right": pad, "Top": pad}
    if pad_x is not None:
        sides["Left"] = sides["Right"] = pad_x
    if pad_y is not None:
        sides["Top"] = sides["Bottom"] = pad_y
    for side in ("Bottom", "Left", "Right", "Top"):
        if sides[side] is not None:
            p[f"Padding{side}"] = sides[side]
    for k, v in (("Visible", visible), ("Width", w), ("Y", y)):
        if v is not None:
            p[k] = v
    return Node(name, "GroupContainer@1.5.0", p, children, variant="AutoLayout")


def hrow(name, children, h, gap=16, fp=0, visible=None, fill=None, pad_x=None, align="Stretch"):
    return box(name, children, "Horizontal", gap, h=h, fp=fp, visible=visible, fill=fill, pad_x=pad_x, align=align)


# ------------------------------------------------------------------ patterns
def chrome(p, title, subtitle, user_expr, tabs, active, title_role=None):
    """Header band, title, subtitle, user, navigation strip, tabs and the current-tab underline, placed ON THE SCREEN (not in a container).
    tabs: [(text, screen_name, visible_expr_or_None), ...]. Names: <p>Hdr, HdrTitle, HdrSub, HdrUser, Nav, TabDash, TabDocs, TabLine.
    user_expr is always a formula (User().FullName), never text. Bands and the underline have an empty text, ="" (not """", a quote mark)."""
    user = _eq(user_expr)
    out = [label(f"{p}Hdr", '=""', size=12, h=HEADER_H, w="Parent.Width", fill="ColorSecondary"),
           label(f"{p}HdrTitle", title, size=18, bold=True, color="ColorOnSecondary", h=TITLE_H, w=500, x=20, y=6, role=title_role),
           label(f"{p}HdrSub", subtitle, size=11, color="ColorOnSecondaryMuted", h=SUB_H, w=500, x=20, y=32),
           label(f"{p}HdrUser", user, size=12, color="ColorOnSecondary", align="Right", h=TITLE_H, w=420, x="Parent.Width - 440", y=14),
           label(f"{p}Nav", '=""', size=12, h=NAV_H, w="Parent.Width", y=HEADER_H, fill="ColorSurface")]
    for i, (text, scr, vis) in enumerate(tabs):
        out.append(button(f"{p}Tab{['Dash', 'Docs', 'Tab3', 'Tab4'][i]}", text, f"Navigate({scr}, ScreenTransition.None)", "tab", w=TAB_W, h=TAB_H,
                          x=TAB_X + i * TAB_STEP, y=TAB_Y, visible=vis, weight=None if i == active else "FontWeight.Normal"))
    out.append(label(f"{p}TabLine", '=""', size=12, h=LINE_H, w=TAB_W, x=TAB_X + active * TAB_STEP, y=LINE_Y, fill="ColorPrimary", visible=tabs[active][2]))
    return out


TOPBAR_H, TOPBAR_TAB_W, TOPBAR_TAB_X = 48, 140, 290


def topbar(p, title, user_expr, tabs, active):
    """The prototype's single-band chrome (single-band header): one band of TOPBAR_H in ColorPrimary with the title at the left, the tabs after it and
    the signed-in user at the right; the active tab is semibold with a 3-high underline. Controls placed ON THE SCREEN, like chrome().
    tabs: [(text_or_formula, screen_name, visible_expr_or_None), ...]. Names: <p>Hdr, HdrTitle, HdrUser, Tab1.., TabLine."""
    out = [label(f"{p}Hdr", '=""', size=12, h=TOPBAR_H, w="Parent.Width", fill="ColorPrimary"),
           label(f"{p}HdrTitle", title, size=18, bold=True, color="ColorOnPrimary", h=TITLE_H, w=250, x=20, y=10),
           label(f"{p}HdrUser", _eq(user_expr), size=12, color="ColorOnPrimary", align="Right", h=TITLE_H, w=360, x="Parent.Width - 380", y=10)]
    for i, (text, scr, vis) in enumerate(tabs):
        b = button(f"{p}Tab{i + 1}", text, f"Navigate({scr}, ScreenTransition.None)", "tab", w=TOPBAR_TAB_W, h=TOPBAR_H, x=TOPBAR_TAB_X + i * TOPBAR_TAB_W, y=0,
                   visible=vis, color="ColorOnPrimary", hover_fill="ColorOnPrimaryHover", pressed_fill="ColorOnPrimaryPressed",
                   weight=None if i == active else "FontWeight.Normal")
        b.props["HoverColor"] = b.props["PressedColor"] = "ColorOnPrimary"
        out.append(b)
    out.append(label(f"{p}TabLine", '=""', size=12, h=LINE_H, w=TOPBAR_TAB_W, x=TOPBAR_TAB_X + active * TOPBAR_TAB_W, y=TOPBAR_H - LINE_H, fill="ColorOnPrimary", visible=tabs[active][2]))
    return out


def body(p, children, pad_div=2, content_w=CONTENT_W, top=BODY_Y, fill="ColorBackground"):
    """The ONE scrolling auto-layout body under the header; sections inside it have an explicit Height and FillPortions 0.
    pad_div 2 centres the 1150-wide content; the sample also uses 4 and 6 (a wider page) on some screens."""
    n = box(f"{p}Main", children, "Vertical", BODY_GAP, h=f"Parent.Height - {top}", w="Parent.Width", y=top, fill=fill, scroll=True,
            pad_x=f"Max(20, (Parent.Width - {content_w}) / {pad_div})", min0=False)
    n.props["PaddingBottom"] = PAD_BOTTOM
    n.props["PaddingTop"] = PAD_TOP
    return n


def title(name, text, size=20, h=36, visible=None, ac=None):
    return label(name, text, size=size, bold=True, h=h, visible=visible, ac=ac)


def heading(name, text, h=26, size=15, visible=None):
    return label(name, text, size=size, bold=True, h=h, visible=visible)


def table_header(name, cols, visible=None, center=False):
    """cols: [(text, fill_portions), ...]. A grey 30-high row; header text is 11-point semibold (centred on the sample's dashboard)."""
    kids = [label(f"{name}H{i}", t, size=11, bold=True, fp=fp, align="Center" if center else None) for i, (t, fp) in enumerate(cols, 1)]
    return hrow(name, kids, TABLE_HEAD_H, 8, 0, visible, "ColorSurface", 8, "Center")


def table(name, items, row_cells, height, tpl=ROW_H, visible=None, ac=None, row_fill="ColorBackground", row_pad=8, row_gap=8):
    """A table body: a gallery in a fixed-height ManualLayout wrapper (height = rows * tpl, or a fixed number), one row container sized to
    the template, and a 1 px separator. Uses the sample's gallery variant and ONLY these gallery properties."""
    row = box(f"{name}Row", row_cells, "Horizontal", row_gap, h="Parent.TemplateHeight", w="Parent.TemplateWidth", fill=row_fill, pad_x=row_pad, align="Center", min0=False)
    sep = Node(f"{name}Sep", "Rectangle@2.3.0", {"BorderColor": "ColorTransparent", "Fill": "ColorDivider", "Height": SEP_H, "Width": "Parent.TemplateWidth",
                                                  "Y": "Parent.TemplateHeight - Self.Height"})
    gal = Node(name, "Gallery@2.15.0", {"BorderColor": "ColorDivider", "Height": "Parent.Height", "Items": _with_comment(items, ac), "TemplateSize": tpl,
                                        "Width": "Parent.Width"}, [row, sep], variant="BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0")
    wp = {"DropShadow": "DropShadow.None", "FillPortions": 0, "Height": height, "LayoutMaxHeight": "", "LayoutMaxWidth": ""}
    if visible:
        wp["Visible"] = visible
    return Node(f"{name}Wrap", "GroupContainer@1.5.0", wp, [gal], variant="ManualLayout")


def cell(name, text, fp, bold=False, align=None, size=12, ac=None):
    """A table cell. align="Center" as on the sample's dashboard; omit for left-aligned columns."""
    return label(name, text, size=size, bold=bold, fp=fp, align=align, align_in="AlignInContainer.Center", ac=ac)


def view_button(name, onselect, fp=0.8, text="View", ac=None):
    return button(name, text, onselect, "secondary", h=SMALL_BTN_H, fp=fp, align_in="AlignInContainer.Center", ac=ac)


def card(name, caption, value_expr, ac=None):
    """A count card: grey, bordered, a 20-high caption over a 24-point semibold number (34 high)."""
    return box(name, [label(f"{name}Cap", caption, size=12, h=20), label(f"{name}Num", value_expr, size=24, bold=True, h=34, ac=ac)], "Vertical", None,
               fill="ColorSurface", pad_x=12, pad_y=8, border=True)


def card_row(name, cards, visible=None):
    return hrow(name, cards, CARD_H, CARD_GAP, 0, visible)


def field(name, caption, control):
    """A labelled input: an 18-high 11-point semibold caption over a 34-high control, 2 apart, in a 56-high column."""
    return box(name, [label(f"{name}Cap", caption, size=11, bold=True, h=18), control], "Vertical", 2, h=FIELD_H)


def field_row(name, fields, visible=None):
    """Three fields a row, 16 apart, 62 high."""
    return hrow(name, fields, FIELD_ROW_H, 16, 0, visible)


def section(name, head, children, height, visible=None, fill="ColorSurface", radius=None, shadow="None", border_color="ColorDivider", pad=12,
            head_size=15, head_h=24, gap=8):
    """A grey bordered section: padding 12, gap 8, a 24-high 15-point heading, then rows. Height is explicit, the sum of its rows plus
    12 + 24 + 8 (head) + 12 + the gaps. Height may be a formula (rows * row height). Do NOT pass None for a section that holds a table, a gallery or rows whose height is a formula:
    Studio does not fit such a section to its content and the card is cut off (PA-T36)."""
    return box(name, [label(f"lbl{name}Head", head, size=head_size, bold=True, h=head_h)] + children, "Vertical", gap, h=height, fp=0, fill=fill, pad=pad,
               border=True, visible=visible, radius=radius, shadow=shadow, border_color=border_color)


def segmented(name, var, options):
    """A choice of few values as buttons: the selected one is filled with the primary colour. 34 high, 4 apart."""
    kids = []
    for i, o in enumerate(options, 1):
        sel = f'{var} = "{o}"'
        kids.append(button(f"{name}{i}", o, f'Set({var}, "{o}")', "secondary", h=CTRL_H, fp=1, color=f"If({sel}, ColorOnPrimary, ColorText)",
                           fill=f"If({sel}, ColorPrimary, ColorBackground)", hover_fill=f"If({sel}, ColorPrimary, ColorSurface)",
                           pressed_fill=f"If({sel}, ColorPrimary, ColorDivider)"))
    return box(name, kids, "Horizontal", 4, h=CTRL_H, fp=0)


def kv(name, key, value_expr):
    """A read-only field: an 18-high muted key over a 24-high semibold value."""
    return box(name, [label(f"{name}K", key, size=10.5, color="ColorTextMuted", h=18), label(f"{name}V", value_expr, bold=True, h=24)], "Vertical", 2)


def note_banner(name, text_expr, visible):
    return label(name, text_expr, size=12, fill="ColorNoteFill", h=44, pad_left=10, border="ColorNoteBorder", visible=visible)


def modal_frame(var, heights, w=MODAL_W, overlay_name="dtlOverlay"):
    """The dimmed overlay and the white panel. heights: {"aon": 330, ..., "_": 300}. Controls of a dialog are placed from the panel
    (modal_x, modal_y, MODAL_BOTTOM_Y) and shown by `var`; the bottom buttons sit at the panel's bottom minus 56."""
    sw = ", ".join(f'"{k}", {v}' for k, v in heights.items() if k != "_") + f", {heights.get('_', 300)}"
    return [label(overlay_name, '=""', size=12, h="Parent.Height", w="Parent.Width", fill="ColorOverlay", visible=f'{var} <> ""'),
            Node("recModalPanel", "Rectangle@2.3.0", {"BorderColor": "ColorDivider", "BorderThickness": 1, "Fill": "ColorBackground", "Height": f"Switch({var}, {sw})",
                                                      "Visible": f'{var} <> ""', "Width": w, "X": f"(Parent.Width - {w}) / 2", "Y": MODAL_Y})]


def modal_x(offset=MODAL_PAD):
    return f"recModalPanel.X + {offset}"


def modal_y(offset):
    return f"recModalPanel.Y + {offset}"


MODAL_BOTTOM_Y = "recModalPanel.Y + recModalPanel.Height - 56"


# ------------------------------------------------------------------ prototype fidelity (docs/standards/prototype-fidelity.md section 8)
# The numbers above are the REFERENCE APP's. When a project has an accepted prototype, its sizes win: measure them with
# tools/prototype_design.py and pass them in through Design. These patterns reproduce what the prototype draws with verified controls only
# (GroupContainer and Image take Radius* and DropShadow; Image shows an SVG). Pending Studio proof: build-plan spike S-UI (ui-patterns section 10).
class Design:
    """A prototype's measurements at the app's scale. scale = app content width / prototype content width (prototype_design.py prints it)."""

    def __init__(self, scale=1.0):
        self.scale = scale

    def pt(self, px):
        """A CSS font size in px as Power Apps points (1 pt = 4/3 px), to the nearest half point."""
        return round(px * self.scale * 0.75 * 2) / 2

    def n(self, px):
        """A CSS length (padding, radius, height, gap) at the app's scale."""
        return int(round(px * self.scale))

    def h(self, px, line_height=1.3, lines=1, pad=0):
        """The height a label needs for a font of `px` CSS px: its lines at the CSS line-height, plus its own padding."""
        return int(-(-self.pt(px) / 0.75 * line_height * lines // 1)) + pad

    def w(self, text, px, bold=False, pad=0):
        """An estimate of a text's width (Segoe UI averages about 0.52 em a character, 0.56 bold), for sizing tabs and pills."""
        return int(len(text) * self.pt(px) / 0.75 * (0.56 if bold else 0.52)) + 2 * pad


def svg_image(name, svg_expr, w, h, x=None, y=None, fp=None, visible=None, accessible="", align_in=None):
    """An Image control showing an SVG built by a formula (svg_expr is a Power Fx text expression). Colours inside the SVG come from the
    Hex<Token> named formulas, never from literals. accessible="" marks a decorative image; give a name when it carries meaning."""
    p = {"AccessibleLabel": f'"{accessible}"', "BorderColor": "ColorTransparent", "Height": h,
         "Image": f'"data:image/svg+xml;utf8," & EncodeUrl({svg_expr})', "ImagePosition": "ImagePosition.Fill", "Width": w}
    for k, v in (("X", x), ("Y", y), ("FillPortions", fp), ("Visible", visible), ("AlignInContainer", align_in)):
        if v is not None:
            p[k] = v
    return Node(name, "Image@2.2.3", p)


def svg_ring(name, pct_expr, size, stroke, track_hex, from_hex, to_hex, text_hex, text_pt, x=None, y=None, align_in=None):
    """A progress ring: a track, a gradient arc of pct_expr (0..100) per cent from the top, and "n%" at its centre (a prototype's SVG ring).
    Its accessible name is "<n> percent"."""
    r = (size - stroke) / 2
    c = round(2 * 3.14159265 * r, 2)
    fpx = round(text_pt / 0.75, 1)
    pct = f"Min(100, Max(0, {pct_expr}))"
    q = "\\\""  # placeholder, replaced below by a real double quote
    svg = (f"\"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 {size} {size}'>"
           f"<defs><linearGradient id='rg' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='{q} & {from_hex} & {q}'/>"
           f"<stop offset='1' stop-color='{q} & {to_hex} & {q}'/></linearGradient></defs>"
           f"<circle cx='{size / 2}' cy='{size / 2}' r='{r}' fill='none' stroke='{q} & {track_hex} & {q}' stroke-width='{stroke}'/>"
           f"<circle cx='{size / 2}' cy='{size / 2}' r='{r}' fill='none' stroke='url(#rg)' stroke-width='{stroke}' stroke-linecap='round' "
           f"stroke-dasharray='{q} & Substitute(Text(Round({pct} * {c} / 100, 2)), {q},{q}, {q}.{q}) & {q} {c}' transform='rotate(-90 {size / 2} {size / 2})'/>"
           f"<text x='50%' y='50%' dominant-baseline='central' text-anchor='middle' font-family='Segoe UI' font-weight='600' font-size='{fpx}' "
           f"fill='{q} & {text_hex} & {q}'>{q} & Round({pct}, 0) & {q}%</text></svg>\"").replace(q, '"')
    node = svg_image(name, svg, size, size, x=x, y=y, align_in=align_in)
    node.props["AccessibleLabel"] = f'Round({pct}, 0) & " percent"'
    return node


def svg_backdrop(name, base_hex, blobs, h="Parent.Height", w="Parent.Width"):
    """A page background: the base colour with soft radial colour blobs (a prototype's body background radial-gradient(...)).
    blobs: [(cx, cy, r, hex_token)] with cx, cy, r as fractions of the page (0.12 = 12%). Put it in Screen.backdrop; the body is then
    transparent so translucent cards show it."""
    defs, rects = [], []
    for i, (cx, cy, r, hx) in enumerate(blobs, 1):
        defs.append(f"<radialGradient id='g{i}' cx='{cx}' cy='{cy}' r='{r}'><stop offset='0' stop-color='\" & {hx} & \"'/>"
                    f"<stop offset='0.7' stop-color='\" & {hx} & \"' stop-opacity='0'/></radialGradient>")
        rects.append(f"<rect width='100' height='100' fill='url(#g{i})'/>")
    svg = ("\"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' preserveAspectRatio='none'><defs>" + "".join(defs) + "</defs>"
           f"<rect width='100' height='100' fill='\" & {base_hex} & \"'/>" + "".join(rects) + "</svg>\"")
    return svg_image(name, svg, w, h, x=0, y=0)


def svg_tile(name, size, radius, from_hex, to_hex, x=None, y=None, mid_hex=None):
    """A small rounded square filled with a gradient (a logo tile)."""
    mid = f"<stop offset='0.6' stop-color='\" & {mid_hex} & \"'/>" if mid_hex else ""
    svg = (f"\"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 {size} {size}'><defs>"
           f"<linearGradient id='t' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='\" & {from_hex} & \"'/>{mid}"
           f"<stop offset='1' stop-color='\" & {to_hex} & \"'/></linearGradient></defs>"
           f"<rect width='{size}' height='{size}' rx='{radius}' fill='url(#t)'/></svg>\"")
    return svg_image(name, svg, size, size, x=x, y=y)


def panel(name, x, y, w, h, fill="ColorGlass", border_color="ColorGlassStroke", radius=0, shadow="Light", visible=None):
    """A rounded, optionally translucent shape with no children (a ManualLayout container): the background of a floating bar or a
    segmented control, with the controls placed over it on the screen (ui-patterns section 3: chrome is never a container of controls)."""
    p = {"BorderColor": border_color, "BorderThickness": 1 if border_color != "ColorTransparent" else 0, "DropShadow": f"DropShadow.{shadow}",
         "Fill": fill, "Height": h, "LayoutMaxHeight": "", "LayoutMaxWidth": ""}
    for k in ("RadiusTopLeft", "RadiusTopRight", "RadiusBottomLeft", "RadiusBottomRight"):
        p[k] = radius
    p.update({"Width": w, "X": x, "Y": y})
    if visible is not None:
        p["Visible"] = visible
    return Node(name, "GroupContainer@1.5.0", p, [], variant="ManualLayout")


def floating_topbar(p, title, user_expr, tabs, active, geo, logo=None):
    """A prototype's floating top bar: a rounded translucent bar (max width geo["w"], geo["top"] from the top) with an optional logo tile and the
    title at the left, the tabs as a segmented pill in the centre and the signed-in user at the right. Controls are placed ON THE SCREEN over
    the bar's panel. tabs: [(text, screen, visible_or_None, width)]; the selected tab is filled ColorSegmentOn, the others are ColorTextMuted.
    geo keys (from tools/prototype_design.py): w, top, h, radius, pad, title_pt, tab_h, tab_pt, seg_pad, user_pt.
    logo: {size, radius, from, to[, mid][, gap]} with Hex tokens. Names: <p>Hdr, <p>HdrLogo, <p>HdrTitle, <p>HdrSeg, <p>Tab1.., <p>HdrUser."""
    g = geo
    bar_x, bar_w = f"(Parent.Width - Min({g['w']}, Parent.Width - 24)) / 2", f"Min({g['w']}, Parent.Width - 24)"
    out = [panel(f"{p}Hdr", bar_x, g["top"], bar_w, g["h"], radius=g["radius"])]
    x = f"{p}Hdr.X + {g['pad']}"
    if logo:
        out.append(svg_tile(f"{p}HdrLogo", logo["size"], logo["radius"], logo["from"], logo["to"], x=x,
                            y=f"{p}Hdr.Y + ({g['h']} - {logo['size']}) / 2", mid_hex=logo.get("mid")))
        x = f"{p}Hdr.X + {g['pad']} + {logo['size']} + {logo.get('gap', 10)}"
    th = int(-(-g["title_pt"] / 0.75 * 1.3 // 1))
    out.append(label(f"{p}HdrTitle", title, size=g["title_pt"], bold=True, h=th, w=260, x=x, y=f"{p}Hdr.Y + ({g['h']} - {th}) / 2", role="Heading1"))
    vis = [v for _, _, v, _ in tabs]
    widths = [wd for *_, wd in tabs]
    seg_w = "(" + " + ".join(f"If({v}, {wd} + 2, 0)" if v else f"{wd + 2}" for v, wd in zip(vis, widths)) + f" - 2 + 2 * {g['seg_pad']})"
    seg_h = g["tab_h"] + 2 * g["seg_pad"]
    out.append(panel(f"{p}HdrSeg", f"{p}Hdr.X + ({p}Hdr.Width - {seg_w}) / 2", f"{p}Hdr.Y + ({g['h']} - {seg_h}) / 2", seg_w, seg_h,
                     fill="ColorSegment", border_color="ColorTransparent", radius=seg_h // 2, shadow="None"))
    for i, (text, scr, v, wd) in enumerate(tabs):
        before = " + ".join(f"If({vv}, {ww} + 2, 0)" if vv else f"{ww + 2}" for vv, ww in zip(vis[:i], widths[:i])) or "0"
        on = i == active
        b = button(f"{p}Tab{i + 1}", text, f"Navigate({scr}, ScreenTransition.None)", "tab", w=wd, h=g["tab_h"],
                   x=f"{p}HdrSeg.X + {g['seg_pad']} + {before}", y=f"{p}HdrSeg.Y + {g['seg_pad']}", visible=v,
                   fill="ColorSegmentOn" if on else "ColorTransparent", color="ColorText" if on else "ColorTextMuted",
                   hover_fill="ColorSegmentOn" if on else "ColorHoverOverlay", pressed_fill="ColorSegmentOn" if on else "ColorPressedOverlay",
                   size=g["tab_pt"], weight=None if on else "FontWeight.Normal", radius="pill")
        b.props["HoverColor"] = b.props["PressedColor"] = "ColorText"
        out.append(b)
    uh = int(-(-g["user_pt"] / 0.75 * 1.3 // 1))
    out.append(label(f"{p}HdrUser", _eq(user_expr), size=g["user_pt"], color="ColorTextMuted", align="Right", h=uh, w=320,
                     x=f"{p}Hdr.X + {p}Hdr.Width - 320 - {g['pad']}", y=f"{p}Hdr.Y + ({g['h']} - {uh}) / 2"))
    return out


def avatar(name, init_expr, size, pt, fill="ColorPrimaryTint", color="ColorPrimary", x=None, y=None, fp=None, visible=None, align_in=None, accessible=None):
    """A round initials badge (a prototype's .avatar): a ModernText of size x size with radius size / 2."""
    n = badge(name, init_expr, fill, fp=fp, w=size, h=size, radius=size // 2, size=pt)
    n.props["Color"] = color
    n.props.update({"PaddingTop": 0, "PaddingBottom": 0, "PaddingLeft": 0, "PaddingRight": 0})
    if accessible is not None:
        n.props["AccessibleLabel"] = accessible
    for k, v in (("X", x), ("Y", y), ("Visible", visible), ("AlignInContainer", align_in)):
        if v is not None:
            n.props[k] = v
    return n


def svg_bar(name, pct_expr, w, h, track_hex, fill_hex, x=None, y=None, align_in=None):
    """A progress bar (a prototype's .bar): a pill track with a pill fill of pct_expr (0..100) per cent. Accessible name "<n> percent"."""
    pct = f"Min(100, Max(0, {pct_expr}))"
    r = h / 2
    svg = (f"\"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>"
           f"<rect width='{w}' height='{h}' rx='{r}' fill='\" & {track_hex} & \"'/>"
           # not Text(x, "0.##"): that leaves a trailing separator ("30."), which is not an SVG number, so the fill is not drawn (PA-T40)
           f"<rect width='\" & Substitute(Text(Round({pct} * {w} / 100, 1)), \",\", \".\") & \"' height='{h}' rx='{r}' fill='\" & {fill_hex} & \"'/></svg>\"")
    node = svg_image(name, svg, w, h, x=x, y=y, align_in=align_in)
    node.props["AccessibleLabel"] = f'Round({pct}, 0) & " percent"'
    return node


def svg_icon(name, paths, hex_expr, size, x=None, y=None, stroke=1.8, visible=None):
    """A line icon from a prototype's inline SVG (viewBox 24, stroke only): paths is the markup between the svg tags, hex_expr a Hex token."""
    svg = (f"\"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='\" & {hex_expr} & \"' stroke-width='{stroke}' "
           f"stroke-linecap='round' stroke-linejoin='round'>{paths}</svg>\"")
    return svg_image(name, svg, size, size, x=x, y=y, visible=visible)


def side_nav(p, brand, items, active, g, visible, on_select_extra="", logo_text="T"):
    """A prototype's left navigation (ui-patterns section 10): a white panel with a right rule, a logo tile and the brand name, then one item
    per page (an icon, the text, the current one filled ColorPrimaryTint). Controls are placed ON THE SCREEN over the panel (chrome is never a
    container of controls). items: [(text, screen, svg_paths)]. g (from tools/prototype_design.py, scaled): w, pad_x, pad_y, gap, logo, logo_r, brand_pt,
    brand_h, item_h, item_gap, item_r, item_pad, icon, text_pt. visible: a formula. Names: <p>Side, SideLine, Logo, LogoT, Brand, NavOn, NavIcon<i>, Nav<i>."""
    w = g["w"]
    out = [panel(f"{p}Side", 0, 0, w, "Parent.Height", fill="ColorSurface", border_color="ColorTransparent", radius=0, shadow="None", visible=visible),
           rect(f"{p}SideLine", "ColorDivider", "Parent.Height", w=1, x=w - 1, y=0, visible=visible),
           svg_tile(f"{p}Logo", g["logo"], g["logo_r"], "HexPrimary", "HexPrimary", x=g["pad_x"] + g["brand_pad"], y=g["pad_y"])]
    out[-1].props["Visible"] = visible
    out.append(label(f"{p}LogoT", logo_text, size=g["text_pt"], bold=True, color="ColorOnPrimary", h=g["logo"], w=g["logo"], x=g["pad_x"] + g["brand_pad"], y=g["pad_y"],
                     align="Center", valign="Middle", visible=visible))
    bx = g["pad_x"] + g["brand_pad"] + g["logo"] + g["brand_gap"]
    out.append(label(f"{p}Brand", brand, size=g["brand_pt"], bold=True, h=g["brand_h"], w=w - bx - g["pad_x"], x=bx, y=g["pad_y"] + (g["logo"] - g["brand_h"]) // 2, visible=visible))
    y0 = g["pad_y"] + g["logo"] + g["gap"]
    iw = w - 2 * g["pad_x"]
    for i, (text, scr, paths) in enumerate(items):
        y = y0 + i * (g["item_h"] + g["item_gap"])
        on = i == active
        if on:
            out.append(panel(f"{p}NavOn", g["pad_x"], y, iw, g["item_h"], fill="ColorPrimaryTint", border_color="ColorTransparent", radius=g["item_r"], shadow="None", visible=visible))
        out.append(svg_icon(f"{p}NavIcon{i + 1}", paths, "HexPrimary" if on else "HexTextMuted", g["icon"], x=g["pad_x"] + g["item_pad"],
                            y=y + (g["item_h"] - g["icon"]) // 2, visible=visible))
        b = button(f"{p}Nav{i + 1}", text, f"Set(varFilter, \"All statuses\"); Set(varMenuOpen, false); {on_select_extra}Navigate({scr}, ScreenTransition.None)", "tab",
                   w=iw, h=g["item_h"], x=g["pad_x"], y=y, visible=visible, color="ColorPrimary" if on else "ColorTextMuted", size=g["text_pt"],
                   weight="FontWeight.Normal", radius=g["item_r"], hover_fill="ColorNeutralFill", pressed_fill="ColorDivider")
        b.props.update({"Align": "Align.Left", "PaddingLeft": g["item_pad"] + g["icon"] + g["brand_gap"], "HoverColor": "ColorText", "PressedColor": "ColorText"})
        out.append(b)
    return out


# ------------------------------------------------------------------ screens
class Screen:
    def __init__(self, name, prefix, title="=AppTitle", subtitle="=AppSubtitle", user_expr='varMyName & "  |  " & If(varIsTreasury, "Treasury", "Requestor")',
                 tabs=None, active_tab=0, on_visible=None, pad_div=2, title_role=None, content_w=CONTENT_W, body_top=BODY_Y, body_fill="ColorBackground"):
        self.name, self.p, self.on_visible, self.pad_div = name, prefix, on_visible, pad_div
        self.content_w, self.body_top, self.body_fill = content_w, body_top, body_fill
        self.backdrop = []  # controls drawn BEHIND everything else (svg_backdrop); the body is then transparent (body_fill="ColorTransparent")
        self.chrome = chrome(prefix, title, subtitle, user_expr, tabs or [("Dashboard", "scrDashboard", None), ("Documents", "scrDocuments", "varIsTreasury")], active_tab, title_role)
        self.body, self.extra = [], []

    def nodes(self):
        return self.backdrop + self.chrome + [body(self.p, self.body, self.pad_div, self.content_w, self.body_top, self.body_fill)] + self.extra

    def yaml(self):
        seen = set()
        for n in _walk(self.nodes()):
            assert n.name not in seen, f"{self.name}: duplicate control name {n.name} (PA2110)"
            seen.add(n.name)
            if n.control.startswith("GroupContainer"):
                assert "LayoutMode" not in n.props, f"{n.name}: LayoutMode is rejected by Studio (PA-T21)"
            if n.control.startswith("ModernText") and isinstance(n.props.get("Height"), int) and n.props["Height"] < 24:
                assert n.props.get("PaddingTop") == 0, f"{n.name}: a short ModernText needs PaddingTop 0, or Studio shows a scrollbar in it (PA-T39)"
            if n.control.startswith("Gallery"):
                assert "Layout" not in n.props, f"{n.name}: Layout is rejected by Studio on this variant (PA-T21)"
        lines = ["Screens:", f"  {self.name}:", "    Properties:", "      Fill: =ColorBackground"]
        if self.on_visible:
            ov = _eq(self.on_visible)
            if NL in ov:
                lines.append("      OnVisible: |-")
                lines += [f"        {ln}" for ln in ov.split(NL)]
            else:
                lines.append(f"      OnVisible: {_q(ov)}")
        lines.append("    Children:")
        for n in self.nodes():
            lines.extend(emit(n, 6))
        return NL.join(lines) + NL

    def write(self, directory):
        Path(directory, f"{self.name}.pa.yaml").write_text(self.yaml(), encoding="utf-8")


# ------------------------------------------------------------------ self-test against the reference app
def _read(text):
    """name -> (control, variant, {prop: value}) from a .pa.yaml, comments ignored."""
    lines = [l for l in text.split(NL) if not l.startswith("#")]
    out, order = {}, []
    for i, l in enumerate(lines):
        m = re.match(r"^(\s*)- (\w+):\s*$", l)
        if not m:
            continue
        d, name = len(m.group(1)), m.group(2)
        ctrl = var = ""
        j = i + 1
        while j < len(lines) and lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) == d + 4 and not lines[j].strip().startswith("Properties"):
            if "Control:" in lines[j]:
                ctrl = lines[j].split("Control:")[1].strip()
            if "Variant:" in lines[j]:
                var = lines[j].split("Variant:")[1].strip()
            j += 1
        props, k = {}, j + 1
        while k < len(lines) and (not lines[k].strip() or len(lines[k]) - len(lines[k].lstrip()) >= d + 6):
            mm = re.match(r"^\s{%d}(\w+): ?(.*)$" % (d + 6), lines[k])
            if mm:
                props[mm.group(1)] = mm.group(2).strip()
            k += 1
        out[name] = (ctrl, var, props)
        order.append(name)
    return out, order


GEOMETRY = {"Height", "Width", "X", "Y", "FillPortions", "Size", "LayoutGap", "LayoutDirection", "PaddingLeft", "PaddingRight", "PaddingTop", "PaddingBottom",
            "TemplateSize", "RadiusTopLeft", "FontWeight", "LayoutAlignItems", "LayoutOverflowY", "DropShadow", "BorderThickness", "Align", "AlignInContainer",
            "LayoutMinHeight", "LayoutMinWidth", "VerticalAlign"}


def _compare(name, sample_text, screen_yaml, require_order=False):
    sample, s_order = _read(sample_text)
    mine, m_order = _read(screen_yaml)
    problems, checked, common = [], 0, 0
    if require_order and s_order != m_order:
        problems.append(f"control order differs: sample-only {[n for n in s_order if n not in mine]}, ours-only {[n for n in m_order if n not in sample]}")
    for n in sample:
        if n not in mine:
            continue
        common += 1
        (c1, v1, p1), (c2, v2, p2) = sample[n], mine[n]
        if (c1, v1) != (c2, v2):
            problems.append(f"{n}: {c1} {v1} != {c2} {v2}")
        for k in GEOMETRY & (set(p1) | set(p2)):
            checked += 1
            if p1.get(k) != p2.get(k):
                problems.append(f"{n}.{k}: sample {p1.get(k)} / ours {p2.get(k)}")
    print(f"  {name}: {common} controls in common, {checked} geometry properties compared, {len(problems)} difference(s)")
    for p in problems:
        print("    DIFF", p)
    return len(problems)


def selftest():
    """Rebuild parts of the reference screens with this module and compare them with the sample, control by control."""
    d = Path(__file__).resolve().parent.parent / "samples" / "powerapp" / "Src"

    def rd(f):
        return (d / f).read_text(encoding="utf-8")

    bad = 0
    print("canvas_ui self-test against samples/powerapp")
    sc = Screen("scrDocuments", "doc", active_tab=1, on_visible="If(!varIsTreasury, Navigate(scrDashboard, ScreenTransition.None))")
    cols = [("File Name", 3), ("Certificate Holder", 2), ("Request ID", 1), ("Document Type", 1.3), ("Version", 0.8), ("Status", 1), ("", 0.7)]
    sc.body = [title("docTitle", "Documents (SharePoint Library)"), table_header("docTblHdr", cols),
               table("galAllDocs", 'SortByColumns(colDocs, "ID", SortOrder.Descending)',
                     [cell("docF", "ThisItem.Title", 3), cell("docH", "ThisItem.CertificateHolder", 2), cell("docR", "ThisItem.RequestID", 1),
                      cell("docT", "ThisItem.DocumentType", 1.3), cell("docV", "ThisItem.Version", 0.8), cell("docS", "ThisItem.DocStatus", 1),
                      view_button("docView", 'Notify("x")', 0.7)], 520, tpl=40)]
    bad += _compare("Documents screen (whole, in order)", rd("scrDocuments.pa.yaml"), sc.yaml(), require_order=True)
    sc = Screen("scrDashboard", "dsh", active_tab=0, pad_div=6)
    sc.body = [hrow("dshTitleRow", [label("dshTitle", '=If(varIsTreasury, "Treasury Dashboard", "Dashboard")', size=20, bold=True, fp=1),
                                    button("dshNew", "+ New COI Request", "Set(varEditing, false)", "primary", w=190, align_in="AlignInContainer.Center", visible="!varIsTreasury")], 40, 16),
               card_row("dshCardsR", [card("dshR1", "Total Requests", "=CountRows(colReqs)"), card("dshR2", "Treasury Review", "=CountRows(colReqs)")], "!varIsTreasury"),
               heading("dshQHead", '=If(varIsTreasury, "COI Request Queue", "My COI Requests")'),
               hrow("dshFilters", [box("dshFSearch", [label("dshFSearchCap", "Search", size=11, bold=True, h=18), textinput("txtQSearch", '""', "ID, project, holder")], "Vertical", 2, h=FIELD_H)],
                    FIELD_ROW_H, 16, visible="varIsTreasury"),
               table_header("dshHdrR", [("Request ID", 1), ("Project Name", 2)], "!varIsTreasury")]
    bad += _compare("Dashboard pieces", rd("scrDashboard.pa.yaml"), sc.yaml())
    sc = Screen("scrForm", "frm", active_tab=0)
    sc.body = [section("frmSecA", "Request Details", [
        field_row("frmR1", [field("frmPPn", "Project Name", textinput("txtPN", "varForm.ProjectName")), field("frmPPoc", "Point of Contact - Email ID", textinput("txtPOC", "varForm.PocEmail"))]),
        field_row("frmR2", [field("frmPLg", "Language", segmented("segLang", "varLang", ["English", "Spanish", "French", "German"]))])], None)]
    bad += _compare("Form section", rd("scrForm.pa.yaml"), sc.yaml())
    print("  OK: identical to the sample" if not bad else f"  {bad} difference(s)")
    return 0 if not bad else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(__doc__)
