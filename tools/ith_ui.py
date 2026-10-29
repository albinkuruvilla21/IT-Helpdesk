"""ith_ui: generates the IT Help canvas app (canvas/ITHelp/Src) with tools/canvas_ui.py. Project-specific.

Every number is the prototype's, measured at scale 1.0 (the prototype is drawn for 1366 px and the app is 1366 px): specs/design-spec.md
sections 3 and 4, specs/prototype-design.json, and Chromium renders (visual_compare.py measure). Colours are tokens (tools/ith_app.py). Layout follows
docs/standards/ui-patterns.md: chrome controls placed on the screen, one scrolling body, explicit heights, tables as galleries in fixed wrappers.

    uv run tools/ith_ui.py            data from the lists (stage G8)
    uv run tools/ith_ui.py --mock     data from the Mock<Entity> named formulas (stages G6 and G7)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canvas_ui import (Node, Screen, avatar, badge, box, button, dropdown, hrow, label, panel, rect, svg_bar, svg_icon, svg_tile, table,  # noqa: E402
                       textinput, _eq)
import ith_app  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "canvas" / "ITHelp" / "Src"
MOCK = "--mock" in sys.argv

# ------------------------------------------------------------------ the prototype's measurements (px at scale 1.0; fonts in points = px x 0.75)
SW = "SideW"                      # 232, or 64 when folded (AC-ITH-03)
TOP_H, PAD, GAP = 60, 20, 14
CTRL, BTN_H = 34, 37
ROW_H, TH_H, FOOT_H = 44, 38, 50
CARD_R, CTRL_R = 10, 8
BODY_PT, SMALL_PT, BADGE_PT, H1_PT, H3_PT, STAT_PT = 10.5, 9, 9.5, 13.5, 10.5, 19.5
BODY_LH, SMALL_LH = 21, 18
NAV_Y0, NAV_PITCH, NAV_H = 64, 41, 37
DRAWER_W, MODAL_W = 580, 560
NL = "\n"

PATHS = {
    "home": "<path d='M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z'/>",
    "list": "<path d='M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01'/>",
    "user": "<circle cx='12' cy='8' r='4'/><path d='M4 21a8 8 0 0 1 16 0'/>",
    "check": "<circle cx='12' cy='12' r='9'/><path d='M8 12l3 3 5-6'/>",
    "book": "<path d='M4 19V5a2 2 0 0 1 2-2h14v16H6a2 2 0 0 0-2 2zm0 0a2 2 0 0 0 2 2h14'/>",
    "gear": "<path d='M4 6h9m4 0h3M4 12h3m4 0h9M4 18h11m4 0h1'/><circle cx='15' cy='6' r='2'/><circle cx='9' cy='12' r='2'/><circle cx='17' cy='18' r='2'/>",
    "search": "<circle cx='11' cy='11' r='7'/><path d='M21 21l-4.3-4.3'/>",
    "bell": "<path d='M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10 21h4'/>",
    "plus": "<path d='M12 5v14M5 12h14'/>",
    "x": "<path d='M6 6l12 12M18 6L6 18'/>",
    "l": "<path d='M15 6l-6 6 6 6'/>",
    "r": "<path d='M9 6l6 6-6 6'/>",
    "menu": "<rect x='3' y='4' width='18' height='16' rx='2'/><path d='M9 4v16'/>",
    "edit": "<path d='M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z'/>",
    "inbox": "<path d='M3 13l3-8h12l3 8v6H3zM3 13h5l1 3h6l1-3h5'/>",
    "sun": "<circle cx='12' cy='12' r='4'/><path d='M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5'/>",
    "moon": "<path d='M21 13A9 9 0 1 1 11 3a7 7 0 0 0 10 10z'/>",
}
NAV_ITEMS = [("Overview", "scrOverview", "home"), ("All tickets", "scrTickets", "list"), ("My tickets", "scrTickets", "user"),
             ("Assigned to me", "scrTickets", "check"), ("Knowledge base", "scrKnowledge", "book"), ("Settings", "scrSettings", "gear")]
TITLES = {"scrOverview": "Overview", "scrKnowledge": "Knowledge base", "scrSettings": "Settings"}

# status and priority colours (design-spec section 2): (text token, fill token)
ST_TXT = 'Switch({v}, "Open", ColorInfo, "In Progress", ColorWarning, "On Hold", ColorNeutralText, "Resolved", ColorSuccess, "Closed", ColorClosed, ColorNeutralText)'
ST_FILL = 'Switch({v}, "Open", ColorInfoFill, "In Progress", ColorWarningFill, "On Hold", ColorNeutralFill, "Resolved", ColorSuccessFill, "Closed", ColorClosedFill, ColorNeutralFill)'
PR_TXT = 'Switch({v}, "Low", ColorNeutralText, "Medium", ColorInfo, "High", ColorHigh, "Critical", ColorError, ColorNeutralText)'
PR_FILL = 'Switch({v}, "Low", ColorNeutralFill, "Medium", ColorInfoFill, "High", ColorHighFill, "Critical", ColorErrorFill, ColorNeutralFill)'
ST_HEX = 'Switch({v}, "Open", HexInfo, "In Progress", HexWarning, "On Hold", HexNeutralText, "Resolved", HexSuccess, "Closed", HexClosed, HexNeutralText)'
PR_HEX = 'Switch({v}, "Low", HexNeutralText, "Medium", HexInfo, "High", HexHigh, "Critical", HexError, HexNeutralText)'

VIS = '!varLoading && varLoadError = ""'


# ------------------------------------------------------------------ small helpers
def lbl(name, text, pt=BODY_PT, bold=False, color="ColorText", h=BODY_LH, wrap=False, **kw):
    n = label(name, text, size=pt, bold=bold, color=color, h=h, **kw)
    if not wrap:
        n.props["Wrap"] = "false"
    return n


def pill(name, text, fill, color, w, h=21, size=BADGE_PT, visible=None, align_in=True):
    """A status or priority pill: ModernText with a rounded fill (design-spec section 6; the prototype's dot is not drawn, DEV-13)."""
    b = badge(name, text, fill, w=w, h=h, radius=12, size=size)
    b.props["Color"] = color
    b.props.update({"AutoHeight": "false", "PaddingTop": 0, "PaddingBottom": 0, "PaddingLeft": 0, "PaddingRight": 0})
    if visible:
        b.props["Visible"] = visible
    if not align_in:
        b.props.pop("AlignInContainer", None)
    return b


def st_pill(name, expr, w=96, **kw):
    return pill(name, "=" + expr, ST_FILL.format(v=expr), ST_TXT.format(v=expr), w, **kw)


def pr_pill(name, expr, w=76, **kw):
    return pill(name, "=" + expr, PR_FILL.format(v=expr), PR_TXT.format(v=expr), w, **kw)


def icon_image(name, key, hex_expr, size, x, y, onselect=None, accessible="", visible=None, tab=-1, display=None):
    n = svg_icon(name, PATHS[key], hex_expr, size, x=x, y=y, visible=visible)
    if onselect:
        n.props["OnSelect"] = onselect
    n.props["AccessibleLabel"] = f'"{accessible}"' if accessible else '""'
    n.props["TabIndex"] = tab
    if display:
        n.props["DisplayMode"] = display
    return n


def icon_button(name, key, accessible, x, y, onselect, hex_expr="HexTextMuted", visible=None, size=34, icon=18, display=None, ac=None):
    """A 34 x 34 ghost button (its text is the accessible name, drawn transparent) with the prototype's line icon over it."""
    b = button(f"{name}B", accessible, onselect if not ac else f"{onselect} // {ac}", "tab", w=size, h=size, x=x, y=y, visible=visible, color="ColorTransparent",
               hover_fill="ColorHover", pressed_fill="ColorDivider", radius=CTRL_R, display=display)
    b.props["HoverColor"] = b.props["PressedColor"] = "ColorTransparent"
    i = icon_image(name, key, hex_expr, icon, f"({x}) + {(size - icon) // 2}", f"({y}) + {(size - icon) // 2}", onselect, "", visible, -1, display)
    return [b, i]


def state_labels(p, what):
    """Loading, error and no-access messages (design-standards section 5); they take no space while hidden."""
    loading = label(f"{p}Loading", f"Loading {what}…", size=BODY_PT, color="ColorTextMuted", h=40, visible="varLoading", fp=0, valign="Middle")
    loading.props["Live"] = "Live.Polite"
    err = label(f"{p}LoadErr", f'=If(varLoadError = "access", "You do not have access to this data.", "The {what} could not be loaded. " & varLoadReason)',
                size=BODY_PT, color="ColorError", h=40, visible='!varLoading && varLoadError <> ""', fp=0, valign="Middle")
    err.props["Live"] = "Live.Polite"
    retry = button(f"{p}Retry", "Try again", "Select(Parent) // reload", "secondary", w=100, h=BTN_H, visible='!varLoading && varLoadError <> ""', fp=0, size=BODY_PT,
                   radius=CTRL_R, weight="FontWeight.Normal", fill="ColorSurface")
    retry.props["OnSelect"] = RELOAD
    return [loading, err, retry]


def empty_label(name, text, visible, h=66):
    n = label(name, text, size=BODY_PT, color="ColorTextMuted", h=h, align="Center", valign="Middle", visible=visible, fp=0)
    n.props["Live"] = "Live.Polite"
    return n


def card_shell(name, children, h=None, fp=None, visible=None):
    return box(name, children, "Vertical", 0, h=h, fp=fp, fill="ColorSurface", border=True, radius=CARD_R, shadow="None", border_color="ColorDivider", visible=visible)


def card_head(name, title_text, right=None, ac=None):
    """The card's header band: padding 12 x 16, h3, an optional small button, a bottom border."""
    kids = [label(f"{name}T", title_text, size=H3_PT, bold=True, h=BODY_LH, fp=1, role="Heading2", valign="Middle", ac=ac)]
    if right:
        kids.append(right)
    return hrow(name, kids, 54 if right else 46, 8, 0, pad_x=16, align="Center")


def divider(name):
    r = rect(name, "ColorDivider", 1)
    r.props["FillPortions"] = 0
    return r


def ro_text(name, text, visible=None, h=63):
    """A read-only multi-line box (full text reachable by scrolling)."""
    t = textinput(name, default=text, h=h, multiline=True, accessible="Comment text", display="DisplayMode.View", visible=visible)
    t.props.update({"Fill": "ColorTransparent", "BorderColor": "ColorTransparent", "BorderThickness": 0, "Size": BODY_PT})
    return t


# ------------------------------------------------------------------ data layer
TICKET_SHAPE = (
    '{ID: ID, Code: "HD-" & ID, Title: Title, Details: Coalesce(TicketDescription, ""), RequesterName: Coalesce(RequesterName, ""), '
    'RequesterEmail: Coalesce(RequesterEmail, ""), Category: Coalesce(TicketCategory, ""), Priority: Coalesce(TicketPriority, ""), '
    'TicketStatus: Coalesce(TicketStatus, "Open"), AssignedToName: Coalesce(AssignedToName, ""), AssignedToEmail: Coalesce(AssignedToEmail, ""), '
    'Created: Created, Modified: Modified, CreatedText: Text(Created, "dd mmm yyyy", "en-GB"), CreatedFull: Text(Created, "dd mmm yyyy, hh:mm", "en-GB"), '
    'ModifiedFull: Text(Modified, "dd mmm yyyy, hh:mm", "en-GB"), PrioIdx: Coalesce(LookUp(colPriority, Title = TicketPriority).SortOrder, 0), '
    'StatIdx: Coalesce(LookUp(colStatus, Title = TicketStatus).SortOrder, 0), IsFinal: Coalesce(LookUp(colStatus, Title = TicketStatus).IsFinal, false)}')
ACT_SHAPE = '{ID: ID, TicketId: TicketId, Code: "HD-" & TicketId, Text: Title, At: Created}'
IGN = " // fx-ignore FX-DELEG lists under 2,000 items by design, data row limit 2,000 (S-DELEG), baseline Q-07 agreed by Albin 2026-10-29"


def load_tickets():
    if MOCK:
        return ('ClearCollect(colTickets, ForAll(If(MockState = "empty", Filter(MockTicket, false), If(IsStaff, MockTicket, Filter(MockTicket, RequesterEmail = User().Email))), '
                + TICKET_SHAPE + "))")
    return ('If(IsStaff,\n    ClearCollect(colTickets, ForAll(SortByColumns(Filter(ITH_Ticket, ID > 0), "ID", SortOrder.Descending), ' + TICKET_SHAPE + ')),\n'
            '    ClearCollect(colTickets, ForAll(SortByColumns(Filter(ITH_Ticket, RequesterEmail = User().Email), "ID", SortOrder.Descending), ' + TICKET_SHAPE + ')))')


def load_activity():
    if MOCK:
        return 'ClearCollect(colActivityAll, ForAll(If(MockState = "empty", Filter(MockActivity, false), MockActivity), ' + ACT_SHAPE + "))"
    return ('ClearCollect(colActivityAll, ForAll(FirstN(SortByColumns(Filter(ITH_TicketActivity, ID > 0), "ID", SortOrder.Descending), 100), ' + ACT_SHAPE + "))")


def reload_block():
    """One block, repeated verbatim wherever data is (re)loaded: on entering a screen and after every write (ui-patterns section 6)."""
    body = (load_tickets() + ";\n    " + load_activity())
    mock_err = 'If(MockState = "error", Set(varLoadError, "error"));\n' if MOCK else ""
    ign = "" if MOCK else IGN
    return (f"Set(varLoading, true);{ign}\nSet(varLoadError, \"\");\n"
            f"IfError(\n    {body};\n    true,\n"
            '    Set(varLoadError, If(FirstError.Kind = ErrorKind.ReadPermission, "access", "error"));\n'
            "    Set(varLoadReason, FirstError.Message));\n" + mock_err + "Set(varLoading, false)")


RELOAD = reload_block()

LOAD_DRAWER = (
    ('ClearCollect(colComments, ForAll(Filter(MockComment, TicketId = varTicket.ID), {Author: AuthorName, AtText: Text(Created, "dd mmm yyyy, hh:mm", "en-GB"), Body: CommentText}));\n'
     'ClearCollect(colTActivity, ForAll(SortByColumns(Filter(MockActivity, TicketId = varTicket.ID), "ID", SortOrder.Descending), {Text: Title, AtText: Text(Created, "dd mmm yyyy, hh:mm", "en-GB")}));\n'
     'ClearCollect(colAttach, Filter(MockAttach, TicketId = varTicket.ID))') if MOCK else
    ('IfError(\n'
     '    ClearCollect(colComments, ForAll(SortByColumns(Filter(ITH_TicketComment, TicketId = varTicket.ID), "ID", SortOrder.Ascending), '
     '{Author: AuthorName, AtText: Text(Created, "dd mmm yyyy, hh:mm", "en-GB"), Body: Coalesce(CommentText, "")}));\n'
     '    ClearCollect(colTActivity, ForAll(SortByColumns(Filter(ITH_TicketActivity, TicketId = varTicket.ID), "ID", SortOrder.Descending), '
     '{Text: Title, AtText: Text(Created, "dd mmm yyyy, hh:mm", "en-GB")}));\n'
     '    ClearCollect(colAttach, ForAll(LookUp(ITH_Ticket, ID = varTicket.ID).Attachments, {Name: DisplayName}));\n'
     '    true,\n'
     '    Notify("The ticket details could not be loaded. " & FirstError.Message, NotificationType.Error))'))


def open_ticket(rec, tail=""):
    """Opens the detail drawer for a ticket record expression (AC-ITH-24). `tail` is more statements; the AC comment goes last, so it never hides them."""
    return (f'Set(varTicket, {rec}); Set(varMenu, ""); Set(varDrawer, true); // fx-ignore FX-DELEG one ticket\'s comments and activity, far under the 2,000 data row limit (S-DELEG)\n'
            f'{LOAD_DRAWER}{tail} // AC-ITH-24.1')


def write_activity(event, text_expr, value_expr='""'):
    """The activity entry that the timeline, the notification list and the email flows read (AC-ITH-28.2). Returns '' in mock mode (a collection is patched)."""
    ticket = "varTicket"
    if MOCK:
        return (f'Collect(MockActivityLive, {{ID: Coalesce(Max(MockActivityLive, ID), 100) + 1, TicketId: {ticket}.ID, Title: {text_expr}, Created: Now()}})')
    return (f'Patch(ITH_TicketActivity, Defaults(ITH_TicketActivity), {{Title: {text_expr}, TicketId: {ticket}.ID, TicketTitle: {ticket}.Title, '
            f'EventType: {{Value: "{event}"}}, EventValue: {value_expr}, ActorName: User().FullName, ActorEmail: User().Email}})')


# ------------------------------------------------------------------ chrome: sidebar and header, placed on every screen
def active_expr(screen):
    if screen == "scrTickets":
        return 'Switch(varView, "all", 1, "mine", 2, 3)'
    return str({"scrOverview": 0, "scrKnowledge": 4, "scrSettings": 5}[screen])


def nav_go(i, scr):
    view = {1: "all", 2: "mine", 3: "assigned"}.get(i)
    pre = f'Set(varView, "{view}"); Set(varPage, 1); ' if view else ""
    return f'{pre}Set(varMenu, ""); Set(varDrawer, false); Set(varModal, ""); Set(varArticle, Blank()); Navigate({scr}, ScreenTransition.None) // AC-ITH-02.2'


def sidebar(p, act):
    n = [panel(f"{p}Side", 0, 0, SW, "Parent.Height", fill="ColorSurface", border_color="ColorTransparent", radius=0, shadow="None"),
         rect(f"{p}SideLine", "ColorDivider", "Parent.Height", w=1, x=f"{SW} - 1", y=0),
         svg_tile(f"{p}Logo", 28, 8, "HexPrimary", "HexPrimary", x=20, y=18),
         label(f"{p}LogoT", "H", size=11, bold=True, color="ColorOnPrimary", h=28, w=28, x=20, y=18, align="Center", valign="Middle"),
         lbl(f"{p}Brand", "Helpdesk", 11, True, h=22, w=150, x=58, y=21, visible="!varCollapsed")]
    n.append(panel(f"{p}NavOn", 12, f"{NAV_Y0} + {NAV_PITCH} * ({act})", f"{SW} - 24", NAV_H, fill="ColorPrimaryTint", border_color="ColorTransparent", radius=CTRL_R, shadow="None"))
    for i, (text, scr, key) in enumerate(NAV_ITEMS):
        y = NAV_Y0 + NAV_PITCH * i
        on = f"({act}) = {i}"
        n.append(Node(f"{p}NavIcon{i + 1}", "Image@2.2.3", svg_icon(f"{p}NavIcon{i + 1}", PATHS[key], f"If({on}, HexAccentText, HexTextMuted)", 18, x=22, y=y + 9).props))
        b = button(f"{p}Nav{i + 1}", text, nav_go(i, scr), "tab", w=f"{SW} - 24", h=NAV_H, x=12, y=y, color=f"If({on}, ColorAccentText, ColorTextMuted)", size=BODY_PT,
                   hover_fill="ColorHover", pressed_fill="ColorDivider", radius=CTRL_R)
        b.props.update({"Align": "Align.Left", "PaddingLeft": 38, "FontWeight": f"If({on}, FontWeight.Semibold, FontWeight.Normal)", "HoverColor": "ColorText", "PressedColor": "ColorText"})
        n.append(b)
        cnt = {2: "MyOpenCount", 3: "AssignedOpenCount"}.get(i)
        if cnt:
            c = pill(f"{p}Cnt{i + 1}", f"={cnt}", f"If({on}, ColorSurface, ColorHover)", "ColorTextMuted", 28, h=18, size=SMALL_PT, visible=f"!varCollapsed && {cnt} > 0")
            c.props.update({"AlignInContainer": "AlignInContainer.Center", "X": f"{SW} - 12 - 10 - 28", "Y": y + 9})
            n.append(c)
    n += [rect(f"{p}ProfLine", "ColorDivider", 1, w=f"{SW} - 24", x=12, y="Parent.Height - 63"),
          avatar(f"{p}ProfAv", "=Initials(User().FullName)", 30, SMALL_PT, fill="ColorPrimaryTint", color="ColorAccentText", x=20, y="Parent.Height - 52", accessible='""'),
          lbl(f"{p}ProfName", "=User().FullName", BODY_PT, True, h=BODY_LH, w=140, x=60, y="Parent.Height - 54", visible="!varCollapsed"),
          lbl(f"{p}ProfRole", "=MyRole", SMALL_PT, False, "ColorTextMuted", h=SMALL_LH, w=140, x=60, y="Parent.Height - 35", visible="!varCollapsed")]
    return n


def header(p, screen):
    rx = "Parent.Width - 20"                       # right edge of the header content
    ax = f"{rx} - 34"                              # profile avatar button
    bx = f"{ax} - 12 - 34"                         # bell
    tx = f"{bx} - 12 - 34"                         # theme toggle
    cx = f"{tx} - 12 - 133"                        # Create ticket
    sx = f"{cx} - 12 - 300"                        # search box
    title = TITLES.get(screen) or '=Switch(varView, "all", "All tickets", "mine", "My tickets", "Assigned to me")'
    crumb_title = '=If(IsBlank(varArticle), "' + TITLES[screen] + '", "Knowledge base / " & varArticle.Title)' if screen == "scrKnowledge" else title
    n = [label(f"{p}Top", '=""', size=BODY_PT, h=TOP_H, w=f"Parent.Width - {SW}", x=SW, y=0, fill="ColorSurface"),
         rect(f"{p}TopLine", "ColorDivider", 1, w=f"Parent.Width - {SW}", x=SW, y=TOP_H - 1)]
    n += icon_button(f"{p}Collapse", "menu", "Collapse sidebar", f"{SW} + 20", 13, "Set(varCollapsed, !varCollapsed) // AC-ITH-03.1")
    crumb = button(f"{p}CrumbHome", "Helpdesk", 'Set(varMenu, ""); Navigate(scrOverview, ScreenTransition.None) // AC-ITH-04.3', "tab", w=66, h=CTRL, x=f"{SW} + 66", y=13,
                   color="ColorTextMuted", size=BODY_PT, weight="FontWeight.Normal", hover_fill="ColorTransparent", pressed_fill="ColorTransparent")
    crumb.props.update({"Align": "Align.Left", "PaddingLeft": 0, "PaddingRight": 0, "HoverColor": "ColorAccentText", "PressedColor": "ColorAccentText", "Visible": "!(Parent.Width < 900)"})
    n += [crumb,
          lbl(f"{p}CrumbTitle", ('="/  " & ' + crumb_title[1:]) if crumb_title.startswith("=") else f'="/  {crumb_title}"', BODY_PT, True, "ColorText", h=BODY_LH, w=380,
              x=f"{SW} + 132", y=19, role="Heading1", ac="AC-ITH-04.2")]
    # search box (AC-ITH-06)
    n += [panel(f"{p}SearchBg", sx, 13, 300, CTRL, fill="ColorSurface", border_color="ColorBorder", radius=CTRL_R, shadow="None"),
          svg_icon(f"{p}SearchIcon", PATHS["search"], "HexTextMuted", 16, x=f"({sx}) + 10", y=21)]
    s = textinput(f"{p}Search", default="varSearch", hint="Search tickets by ID or subject", h=CTRL, accessible="Search tickets", x=f"({sx}) + 1", y=13, w=298,
                  onchange=SEARCH_CHANGE.format(box=f"{p}Search"))
    s.props.update({"Fill": "ColorTransparent", "BorderColor": "ColorTransparent", "BorderThickness": 0, "PaddingLeft": 34, "DelayOutput": "true", "FocusedBorderColor": "ColorPrimary",
                    "FocusedBorderThickness": 2, "RadiusBottomLeft": CTRL_R, "RadiusBottomRight": CTRL_R, "RadiusTopLeft": CTRL_R, "RadiusTopRight": CTRL_R, "Size": BODY_PT})
    n.append(s)
    # Create ticket (AC-ITH-04.4)
    n.append(button(f"{p}Create", "Create ticket", OPEN_FORM_NEW, "primary", w=133, h=BTN_H, x=cx, y=12, size=BODY_PT, radius=CTRL_R, weight="FontWeight.Semibold"))
    # theme toggle (AC-ITH-08)
    n += icon_button(f"{p}Theme", "x", "Toggle dark theme", tx, 13, "x")                # replaced below: the icon follows the scheme
    n[-2].props["OnSelect"] = 'Set(varMenu, ""); ClearCollect(colScheme, {Value: If(IsDark, "Light", "Dark")}) // AC-ITH-08.1'
    n[-1] = Node(f"{p}ThemeI", "Image@2.2.3", icon_image(f"{p}ThemeI", "moon", "HexTextMuted", 18, f"({tx}) + 8", 21, n[-2].props["OnSelect"], "", None).props)
    n[-1].props["Image"] = ('"data:image/svg+xml;utf8," & EncodeUrl("<svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'" & HexTextMuted & "\' '
                            'stroke-width=\'1.8\' stroke-linecap=\'round\' stroke-linejoin=\'round\'>" & If(IsDark, "' + PATHS["sun"] + '", "' + PATHS["moon"] + '") & "</svg>")')
    n[-2].props["OnSelect"] = n[-1].props["OnSelect"] = 'Set(varMenu, ""); ClearCollect(colScheme, {Value: If(IsDark, "Light", "Dark")}) // AC-ITH-08.1'
    # bell (AC-ITH-07)
    n += icon_button(f"{p}Bell", "bell", "Notifications", bx, 13, 'Set(varMenu, If(varMenu = "notif", "", "notif")); Set(varNotifRead, true) // AC-ITH-07.1')
    n.append(pill(f"{p}BellDot", '=""', "ColorDot", "ColorTransparent", 8, h=8, visible="!varNotifRead && CountRows(RecentActivity) > 0"))
    n[-1].props.update({"X": f"({bx}) + 20", "Y": 19, "AlignInContainer": "AlignInContainer.Center"})
    # profile (AC-ITH-05)
    n.append(button(f"{p}ProfBtn", "Profile", 'Set(varMenu, If(varMenu = "profile", "", "profile")) // AC-ITH-05.2', "tab", w=34, h=34, x=ax, y=13, color="ColorTransparent",
                    hover_fill="ColorHover", pressed_fill="ColorDivider", radius=17))
    n[-1].props["HoverColor"] = n[-1].props["PressedColor"] = "ColorTransparent"
    n.append(avatar(f"{p}ProfAv2", "=Initials(User().FullName)", 30, SMALL_PT, fill="ColorPrimaryTint", color="ColorAccentText", x=f"({ax}) + 2", y=15, accessible='""'))
    n[-1].props["OnSelect"] = n[-2].props["OnSelect"]
    # menus
    px_ = f"({bx}) + 34 - 300"
    ph = "12 + Max(1, Min(5, CountRows(RecentActivity))) * 64"
    n.append(panel(f"{p}NotifPanel", px_, 53, 300, ph, fill="ColorSurface", border_color="ColorDivider", radius=CARD_R, shadow="Bold", visible='varMenu = "notif"'))
    notif_cells = [box(f"{p}NotifTxt", [lbl(f"{p}NotifA", "=ThisItem.Text", BODY_PT, False, "ColorText", h=BODY_LH), lbl(f"{p}NotifB", '=ThisItem.Code & " · " & RelTime(ThisItem.At)', SMALL_PT,
                                                                                             False, "ColorTextMuted", h=SMALL_LH)], "Vertical", 2, fp=1)]
    gal = table(f"{p}NotifGal", "FirstN(RecentActivity, 5)", notif_cells, f"Min(5, CountRows(RecentActivity)) * 64", tpl=64, visible='varMenu = "notif"', ac="AC-ITH-07.2",
                row_fill="ColorSurface", row_pad=10, row_gap=8)
    gal.props.update({"X": px_ + " + 6", "Y": 59, "Width": 288})
    gal.children[0].props["OnSelect"] = open_ticket("LookUp(colTickets, ID = ThisItem.TicketId)", '; Set(varMenu, "")')
    n.append(gal)
    n.append(empty_label(f"{p}NotifEmpty", "No recent activity.", 'varMenu = "notif" && CountRows(RecentActivity) = 0', h=40))
    n[-1].props.update({"X": px_ + " + 6", "Y": 59, "Width": 288, "FillPortions": ""})
    n[-1].props.pop("FillPortions")
    n.append(panel(f"{p}ProfPanel", f"({ax}) + 34 - 300", 53, 300, 12 + 55 + 37, fill="ColorSurface", border_color="ColorDivider", radius=CARD_R, shadow="Bold", visible='varMenu = "profile"'))
    n += [lbl(f"{p}ProfPName", "=User().FullName", BODY_PT, True, h=BODY_LH, w=270, x=f"({ax}) + 34 - 300 + 16", y=53 + 14, visible='varMenu = "profile"'),
          lbl(f"{p}ProfPMail", "=User().Email", SMALL_PT, False, "ColorTextMuted", h=SMALL_LH, w=270, x=f"({ax}) + 34 - 300 + 16", y=53 + 35, visible='varMenu = "profile"')]
    st = button(f"{p}ProfSettings", "Settings", 'Set(varMenu, ""); Navigate(scrSettings, ScreenTransition.None) // AC-ITH-05.2', "tab", w=288, h=NAV_H, x=f"({ax}) + 34 - 300 + 6", y=53 + 6 + 55,
                visible='varMenu = "profile"', size=BODY_PT, weight="FontWeight.Normal", hover_fill="ColorHover", radius=6)
    st.props.update({"Align": "Align.Left", "PaddingLeft": 10})
    n.append(st)
    return n


SEARCH_CHANGE = ('Set(varSearch, {box}.Text); Set(varPage, 1); If(!(App.ActiveScreen.Name = "scrTickets"), Set(varView, "all"); Navigate(scrTickets, ScreenTransition.None)) '
                 '// AC-ITH-06.2')
FORM_NEW = ('Set(varFormMode, "new"); Set(varErrSubject, false); Set(varErrDesc, false); Set(varErrEmail, false); Set(varMenu, ""); '
                 'Set(varModal, "form"); Set(varFormKey, varFormKey + 1)')
OPEN_FORM_NEW = FORM_NEW + " // AC-ITH-20.1"
FORM_EDIT = ('Set(varFormMode, "edit"); Set(varErrSubject, false); Set(varErrDesc, false); Set(varErrEmail, false); Set(varMenu, ""); '
                  'Set(varModal, "form"); Set(varFormKey, varFormKey + 1)')
OPEN_FORM_EDIT = FORM_EDIT + " // AC-ITH-26.1"


import re


class ItScreen(Screen):
    def __init__(self, name, prefix, on_visible):
        super().__init__(name, prefix, on_visible=on_visible)
        self.chrome = []
        self.content = []
        self.overlays = []

    def nodes(self):
        main = box(f"{self.p}Main", self.content, "Vertical", GAP, h=f"Parent.Height - {TOP_H}", w=f"Parent.Width - {SW}", y=TOP_H, fill="ColorBackground", scroll=True, min0=False)
        main.props.update({"X": SW, "PaddingTop": PAD, "PaddingBottom": PAD, "PaddingLeft": PAD, "PaddingRight": PAD})
        return [main] + sidebar(self.p, active_expr(self.name)) + header(self.p, self.name) + self.overlays

    def write(self, directory):
        """Control names are unique across the whole app (PA2110, FX-DUPNAME): the overlay set is on every screen, so its names (pnForm, fm*, pnConfirm, cf*) get the screen's prefix."""
        text = self.yaml()
        p = self.p
        no_word = "(?<![A-Za-z0-9_])"          # a name starts here, not inside a longer word
        text = re.sub(no_word + "pnForm(?![A-Za-z0-9_])", p + "PnForm", text)
        text = re.sub(no_word + "pnConfirm(?![A-Za-z0-9_])", p + "PnConfirm", text)
        text = re.sub(no_word + "fm([A-Z][A-Za-z0-9_]*)", lambda m: p + "Fm" + m.group(1), text)
        text = re.sub(no_word + "cf([A-Z][A-Za-z0-9_]*)", lambda m: p + "Cf" + m.group(1), text)
        Path(directory, f'{self.name}.pa.yaml').write_text(text, encoding='utf-8')


def on_visible(extra=""):
    return 'Set(varMenu, "");\n' + (extra + "\n" if extra else "") + RELOAD


def page_head(p, title_text, sub_expr, tools=None, ac=None, role=True):
    left = box(f"{p}HeadL", [label(f"{p}Title", title_text, size=H1_PT, bold=True, h=27, role="Heading1", ac=ac), label(f"{p}Sub", sub_expr, size=BODY_PT, color="ColorTextMuted", h=BODY_LH)],
               "Vertical", 0, fp=1)
    return hrow(f"{p}Head", [left] + (tools or []), 48, 8, 0, align="Center")


# ------------------------------------------------------------------ scrOverview
def mini_cells(p, key):
    return [lbl(f"{p}{key}Id", "=ThisItem.Code", BODY_PT, True, "ColorAccentText", fp=1.1),
            lbl(f"{p}{key}Sub", '=If(Len(ThisItem.Title) > 38, Left(ThisItem.Title, 37) & "…", ThisItem.Title)', BODY_PT, False, fp=3),
            pr_pill(f"{p}{key}Pr", "ThisItem.Priority", 76), st_pill(f"{p}{key}St", "ThisItem.TicketStatus", 96)]


def mini_list(p, key, head, items, empty_ac, view_all, ac_rows, rowfp=1, card_h=None):
    n = f"CountRows({items})"
    btn = button(f"{p}{key}All", "View all", view_all, "secondary", w=70, h=29, size=BODY_PT, radius=6, weight="FontWeight.Semibold", fill="ColorSurface", align_in="AlignInContainer.Center")
    btn.props["FillPortions"] = 0
    tbl = table(f"{p}{key}Tbl", items, mini_cells(p, key), f"{n} * {ROW_H}", tpl=ROW_H, visible=f"{n} > 0", ac=ac_rows, row_fill="ColorSurface", row_pad=14, row_gap=10)
    tbl.children[0].props["OnSelect"] = open_ticket("ThisItem")
    emp = empty_label(f"{p}{key}Empty", "Nothing here yet.", f"{n} = 0", h=60)
    return card_shell(f"{p}{key}", [card_head(f"{p}{key}Hd", head, btn), divider(f"{p}{key}Div"), tbl, emp], h=card_h or f"54 + 1 + If({n} = 0, 60, {n} * {ROW_H})", fp=rowfp)


def overview():
    p = "ovw"
    s = ItScreen("scrOverview", p, on_visible())
    # the link in the notification emails ends in ?ticket=<id>: open that ticket once the tickets are loaded (AC-ITH-32.2)
    link = ("If(!IsBlank(Param(\"ticket\")) && !varLinkDone,\n  Set(varLinkDone, true);\n  With({id: IfError(Value(Param(\"ticket\")), 0)}, If(!IsBlank(LookUp(colTickets, ID = id)),\n    "
            + open_ticket("LookUp(colTickets, ID = id)", ")))").replace(NL, NL + "    ") + "")
    s.on_visible = s.on_visible + ";" + NL + link.replace("// AC-ITH-24.1", "// AC-ITH-32.2")
    stats = []
    for i, (cap, expr, ac) in enumerate([("Total tickets", "=CountRows(colTickets)", "AC-ITH-11.2"), ("Open", '=CountRows(Filter(colTickets, TicketStatus = "Open"))', "AC-ITH-11.2"),
                                         ("In progress", '=CountRows(Filter(colTickets, TicketStatus = "In Progress"))', "AC-ITH-11.2"),
                                         ("Resolved today", "=ResolvedToday", "AC-ITH-11.2")], 1):
        stats.append(box(f"{p}Stat{i}", [lbl(f"{p}Stat{i}Cap", cap, BODY_PT, False, "ColorTextMuted", h=BODY_LH),
                                         label(f"{p}Stat{i}Val", expr, size=STAT_PT, bold=True, h=32, ac=ac)],
                         "Vertical", 0, fp=1, fill="ColorSurface", pad=16, border=True, radius=CARD_R, shadow="None", border_color="ColorDivider"))
    stat_row = hrow(f"{p}Stats", stats, 84, GAP, 0, VIS)

    recent = mini_list(p, "Rc", "Recent tickets", "RecentTickets", "AC-ITH-12.5", 'Set(varView, "all"); Set(varPage, 1); Navigate(scrTickets, ScreenTransition.None) // AC-ITH-12.3',
                       "AC-ITH-12.1", rowfp=2, card_h=400)
    # tickets by status and by priority (AC-ITH-13)
    bars = []
    for i in range(5):
        v = f"Index(colStatusOpt, {i + 1}).Value"
        bars.append(hrow(f"{p}Sb{i + 1}", [lbl(f"{p}Sb{i + 1}N", "=" + v, BODY_PT, False, w=90, fp=0),
                                           box(f"{p}Sb{i + 1}Track", [svg_bar(f"{p}Sb{i + 1}Bar", f"CountRows(Filter(colTickets, TicketStatus = {v})) * 100 / Max(1, CountRows(colTickets))", 150, 8,
                                                                               "HexHover", ST_HEX.format(v=v), align_in="AlignInContainer.Center")], "Horizontal", 0, fp=1, align="Center"),
                                           lbl(f"{p}Sb{i + 1}C", f"=CountRows(Filter(colTickets, TicketStatus = {v}))", BODY_PT, True, w=28, fp=0, align="Right")],
                         29, 10, 0, visible=f"CountRows(colStatusOpt) >= {i + 1}", align="Center"))
        bars[-1].children[0].props["Width"] = 90
        bars[-1].children[2].props["Width"] = 28
    # priority stacked bar: four segments by FillPortions
    segs = []
    for i in range(4):
        v = f"Index(colPriorityOpt, {i + 1}).Value"
        seg = rect(f"{p}Pb{i + 1}", PR_TXT.format(v=v), 12)
        seg.props["FillPortions"] = f"Max(0.001, CountRows(Filter(colTickets, Priority = {v}))) // AC-ITH-13.2"
        seg.props["Visible"] = f"CountRows(colPriorityOpt) >= {i + 1}"
        segs.append(seg)
    stack = hrow(f"{p}PbRow", segs, 12, 2, 0)
    stack.props.update({"RadiusTopLeft": 6, "RadiusTopRight": 6, "RadiusBottomLeft": 6, "RadiusBottomRight": 6})
    legend = [lbl(f"{p}Lg{i + 1}", f'=Index(colPriorityOpt, {i + 1}).Value & " " & CountRows(Filter(colTickets, Priority = Index(colPriorityOpt, {i + 1}).Value))', BODY_PT, False, fp=1,
                  visible=f"CountRows(colPriorityOpt) >= {i + 1}") for i in range(4)]
    leg_row = hrow(f"{p}LgRow", legend, 21, 16, 0)
    alt = lbl(f"{p}PbAlt", '="Priority split: " & Concat(colPriorityOpt, Value & " " & CountRows(Filter(colTickets, Priority = Value)), ", ")', SMALL_PT, False, "ColorTextMuted", h=SMALL_LH,
              visible="false")
    by = card_shell(f"{p}By", [lbl(f"{p}ByT", "Tickets by status", H3_PT, True, h=BODY_LH, role="Heading2")] + bars +
                    [lbl(f"{p}ByT2", "Tickets by priority", H3_PT, True, h=BODY_LH, role="Heading2"), stack, leg_row, alt], h=None, fp=1)
    by.props.update({"PaddingLeft": 16, "PaddingRight": 16, "PaddingTop": 16, "PaddingBottom": 16, "LayoutGap": 8})
    row2 = hrow(f"{p}Row2", [recent, by], 400, GAP, 0, VIS, align="Stretch")

    mine = mini_list(p, "As", "My assigned tickets", "MyAssigned", "AC-ITH-12.5", 'Set(varView, "assigned"); Set(varPage, 1); Navigate(scrTickets, ScreenTransition.None) // AC-ITH-12.3', "AC-ITH-12.2")
    ev_cells = [svg_bar(f"{p}EvDotBg", "0", 8, 8, "HexAccentText", "HexAccentText", align_in="AlignInContainer.Start"),
                box(f"{p}EvTxt", [lbl(f"{p}EvA", "=ThisItem.Text", BODY_PT, False, "ColorText", h=BODY_LH), lbl(f"{p}EvB", '=ThisItem.Code & " · " & RelTime(ThisItem.At)', SMALL_PT, False,
                                                                                                   "ColorTextMuted", h=SMALL_LH)], "Vertical", 0, fp=1)]
    ev_cells[0].props["Width"] = 8
    ev_cells[0].props.pop("AlignInContainer", None)
    ev_cells[0].props["AlignInContainer"] = "AlignInContainer.Start"
    ev_cells[0].props["Y"] = 0
    ev_n = "CountRows(FirstN(RecentActivity, 7))"
    ev_tbl = table(f"{p}EvTbl", "FirstN(RecentActivity, 7)", ev_cells, f"{ev_n} * 55", tpl=55, visible=f"{ev_n} > 0", ac="AC-ITH-14.1", row_fill="ColorSurface", row_pad=16, row_gap=10)
    act = card_shell(f"{p}Ev", [card_head(f"{p}EvHd", "Recent activity"), divider(f"{p}EvDiv"), ev_tbl, empty_label(f"{p}EvEmpty", "No recent activity.", f"{ev_n} = 0", h=60)],
                     h=f"46 + 1 + If({ev_n} = 0, 60, {ev_n} * 55)", fp=1)
    row3 = hrow(f"{p}Row3", [mine, act], f"Max(54 + 1 + If(CountRows(MyAssigned) = 0, 60, CountRows(MyAssigned) * {ROW_H}), 46 + 1 + If({ev_n} = 0, 60, {ev_n} * 55))", GAP, 0, VIS)
    s.content = [*state_labels(p, "tickets"), stat_row, row2, row3]
    s.overlays = overlays(p)
    return s


# ------------------------------------------------------------------ scrTickets
# (header, sort key, FillPortions or None, fixed width or None): a pill column has the pill's width in the header and in every row
COLS = [("Ticket ID", "ID", 1.1, None), ("Subject", "Title", 3, None), ("Requester", "RequesterName", 1.6, None), ("Category", "Category", 1.2, None), ("Priority", "PrioIdx", None, 76),
        ("Assigned to", "AssignedToName", 1.6, None), ("Status", "StatIdx", None, 96), ("Created", "Created", 1.2, None)]


def filter_dd(p, key, items, var, label_text, w):
    d = dropdown(f"{p}{key}", items)
    d.props.update({"AccessibleLabel": f'"{label_text}"', "Default": f'Coalesce(LookUp({items}, Value = {var}), First({items}))', "FillPortions": 0, "Width": w,
                    "OnChange": f'Set({var}, If({p}{key}.Selected.Value = First({items}).Value, "", {p}{key}.Selected.Value)); Set(varPage, 1) // AC-ITH-16.2',
                    "AlignInContainer": "AlignInContainer.Center"})
    return d


def tickets():
    p = "tk"
    s = ItScreen("scrTickets", p, on_visible())
    export = button(f"{p}Export", "Export CSV", 'Download("data:text/csv;charset=utf-8," & EncodeUrl(CsvText)) // AC-ITH-42.1', "secondary", w=104, h=BTN_H, size=BODY_PT, radius=CTRL_R,
                    weight="FontWeight.Semibold", fill="ColorSurface", visible="IsStaff", fp=0, align_in="AlignInContainer.Center")
    head = page_head(p, '=Switch(varView, "all", "All tickets", "mine", "My tickets", "Assigned to me")',
                     '=Switch(varView, "all", "Every ticket in the helpdesk.", "mine", "Tickets you submitted as " & User().FullName & ".", "Tickets assigned to you.")',
                     [export], ac="AC-ITH-15.1")
    # toolbar
    sb = panel(f"{p}SearchBg", 0, 0, 280, CTRL, fill="ColorSurface", border_color="ColorBorder", radius=CTRL_R, shadow="None")
    search = textinput(f"{p}Search2", default="varSearch", hint="Search by ID or subject", h=CTRL, accessible="Search tickets", w=280, fp=0, onchange=f"Set(varSearch, {p}Search2.Text); Set(varPage, 1) // AC-ITH-16.1")
    search.props.update({"Fill": "ColorSurface", "BorderColor": "ColorBorder", "BorderThickness": 1, "PaddingLeft": 12, "DelayOutput": "true", "FocusedBorderColor": "ColorPrimary",
                         "FocusedBorderThickness": 2, "RadiusBottomLeft": CTRL_R, "RadiusBottomRight": CTRL_R, "RadiusTopLeft": CTRL_R, "RadiusTopRight": CTRL_R, "Size": BODY_PT,
                         "AlignInContainer": "AlignInContainer.Center"})
    clear = button(f"{p}Clear", "Clear filters", 'Set(varSearch, ""); Set(varFStatus, ""); Set(varFPriority, ""); Set(varFCategory, ""); Set(varPage, 1); Reset(' + f"{p}Search2" + ') // AC-ITH-16.5',
                   "tab", w=110, h=BTN_H, size=BODY_PT, radius=CTRL_R, weight="FontWeight.Semibold", fp=0, align_in="AlignInContainer.Center", color="ColorTextMuted")
    clear.props["HoverFill"] = "ColorHover"
    tb = hrow(f"{p}Tb", [search, filter_dd(p, "FSt", "colFStatus", "varFStatus", "Status", 150), filter_dd(p, "FPr", "colFPriority", "varFPriority", "Priority", 150),
                         filter_dd(p, "FCa", "colFCategory", "varFCategory", "Category", 150), clear], 40, 10, 0, VIS, align="Center")
    # table header: sortable buttons
    heads = []
    for i, (text, key, fp, fw) in enumerate(COLS, 1):
        b = button(f"{p}Th{i}", f'="{text}" & If(varSort = "{key}", If(varDesc, " ▼", " ▲"), "")',
                   f'If(varSort = "{key}", Set(varDesc, !varDesc), Set(varSort, "{key}"); Set(varDesc, false)) // AC-ITH-17.1', "tab", h=TH_H, fp=(fp if fw is None else 0), w=fw, size=SMALL_PT + 0.5, color="ColorTextMuted",
                   weight="FontWeight.Normal", hover_fill="ColorTransparent", pressed_fill="ColorTransparent")
        b.props.update({"Align": "Align.Left", "PaddingLeft": 0, "PaddingRight": 0, "HoverColor": "ColorText", "PressedColor": "ColorText", "RadiusTopLeft": 0, "RadiusTopRight": 0,
                        "RadiusBottomLeft": 0, "RadiusBottomRight": 0, "Text": b.props["Text"]})
        b.props.update({"LayoutMinWidth": 0, "LayoutMinHeight": 0})  # a Classic button has a minimum width, so the header row would overflow its card
        heads.append(b)
    heads.append(lbl(f"{p}ThAct", "Actions", SMALL_PT + 0.5, False, "ColorTextMuted", h=TH_H, w=64, fp=0, valign="Middle"))
    th = hrow(f"{p}Th", heads, TH_H, 8, 0, "CountRows(PagedTickets) > 0", "ColorSunken", 14, "Center")
    cells = [lbl(f"{p}RId", "=ThisItem.Code", BODY_PT, True, "ColorAccentText", fp=1.1),
             lbl(f"{p}RSub", '=If(Len(ThisItem.Title) > 38, Left(ThisItem.Title, 37) & "…", ThisItem.Title)', BODY_PT, False, fp=3, ac="AC-ITH-15.3"),
             lbl(f"{p}RReq", "=ThisItem.RequesterName", BODY_PT, False, fp=1.6), lbl(f"{p}RCat", "=ThisItem.Category", BODY_PT, False, fp=1.2),
             pr_pill(f"{p}RPr", "ThisItem.Priority", 76),
             lbl(f"{p}RAs", '=If(IsBlank(ThisItem.AssignedToName), "Unassigned", ThisItem.AssignedToName)', BODY_PT, False, "If(IsBlank(ThisItem.AssignedToName), ColorTextMuted, ColorText)", fp=1.6),
             st_pill(f"{p}RSt", "ThisItem.TicketStatus", 96),
             lbl(f"{p}RCr", "=ThisItem.CreatedText", BODY_PT, False, fp=1.2)]
    ed_btn = button(f"{p}REd", "Edit", open_ticket("ThisItem", "; " + FORM_EDIT), "tab", h=29, w=64, fp=0, size=SMALL_PT + 0.5, visible="IsStaff", color="ColorAccentText",
                    weight="FontWeight.Normal", hover_fill="ColorHover", radius=6, align_in="AlignInContainer.Center")
    cells.append(ed_btn)
    n = "CountRows(PagedTickets)"
    tbl = table(f"{p}Tbl", "PagedTickets", cells, f"{n} * {ROW_H}", tpl=ROW_H, visible=f"{n} > 0", ac="AC-ITH-15.2", row_fill="ColorSurface", row_pad=14, row_gap=8)
    tbl.children[0].props["OnSelect"] = open_ticket("ThisItem")
    # footer (AC-ITH-17.3)
    foot_kids = [lbl(f"{p}FCount", '=If(CountRows(FilteredTickets) = 0, "0", ((varPage - 1) * varPageSize + 1) & "–" & ((varPage - 1) * varPageSize + CountRows(PagedTickets)) & " of " & CountRows(FilteredTickets))',
                     BODY_PT, False, "ColorTextMuted", fp=1, ac="AC-ITH-17.3"),
                 lbl(f"{p}FRows", "Rows", BODY_PT, False, "ColorTextMuted", w=52, fp=0)]
    rows_dd = dropdown(f"{p}FSize", "colPageSizes")
    rows_dd.props.update({"AccessibleLabel": '"Rows per page"', "Default": "LookUp(colPageSizes, Value = varPageSize)", "FillPortions": 0, "Width": 80, "AlignInContainer": "AlignInContainer.Center",
                          "OnChange": f"Set(varPageSize, {p}FSize.Selected.Value); Set(varPage, 1) // AC-ITH-17.5"})
    prev = icon_image(f"{p}Prev", "l", "HexText", 18, None, None, "Set(varPage, varPage - 1) // AC-ITH-17.4", "Previous page", tab=0, display="If(varPage < 2, DisplayMode.Disabled, DisplayMode.Edit)")
    nxt = icon_image(f"{p}Next", "r", "HexText", 18, None, None, "Set(varPage, varPage + 1) // AC-ITH-17.4", "Next page", tab=0, display="If(varPage >= PageCount, DisplayMode.Disabled, DisplayMode.Edit)")
    prev.props.update({"AlignInContainer": "AlignInContainer.Center", "FillPortions": 0, "Transparency": "If(varPage < 2, 0.6, 0)", "HoverFill": "ColorHover"})
    nxt.props.update({"AlignInContainer": "AlignInContainer.Center", "FillPortions": 0, "Transparency": "If(varPage >= PageCount, 0.6, 0)", "HoverFill": "ColorHover"})
    foot = hrow(f"{p}Foot", foot_kids + [rows_dd, prev, lbl(f"{p}FPage", '=varPage & " / " & PageCount', BODY_PT, False, "ColorTextMuted", w=60, fp=0, align="Center"), nxt], FOOT_H, 10, 0, "CountRows(PagedTickets) > 0",
                pad_x=14, align="Center")
    emp_filter = 'CountRows(FilteredTickets) = 0'
    f_on = '!IsBlank(Trim(varSearch)) || varFStatus <> "" || varFPriority <> "" || varFCategory <> ""'
    ic = svg_icon(f"{p}EmptyI", PATHS["inbox"], "HexTextMuted", 32, x=0, y=0)
    ic.props["AlignInContainer"] = "AlignInContainer.Center"
    eb = button(f"{p}EmptyB", f'=If({f_on}, "Clear filters", "Create ticket")', f"If({f_on}, Select({p}Clear), {FORM_NEW}) // AC-ITH-18.1", "secondary", w=130, h=BTN_H, size=BODY_PT,
                radius=CTRL_R, weight="FontWeight.Semibold", fill="ColorSurface", align_in="AlignInContainer.Center")
    empty = box(f"{p}Empty", [ic, label(f"{p}EmptyH", f'=If({f_on}, "No tickets match your filters", "No tickets here yet")', size=H3_PT, bold=True, h=BODY_LH, align="Center"),
                              label(f"{p}EmptyT", f'=If({f_on}, "Try a different search or clear the filters.", "Create a ticket to get started.")', size=BODY_PT, color="ColorTextMuted", h=BODY_LH, align="Center"),
                              eb], "Vertical", 8, h=200, fp=0, visible=emp_filter, align="Center", pad_y=32)
    for child in empty.children:
        if child.name.endswith(("EmptyH", "EmptyT")):
            child.props.update({"Width": 420, "AlignInContainer": "AlignInContainer.Center"})
    card = card_shell(f"{p}Card", [th, tbl, foot, empty], h=f"If({n} = 0, 200, {TH_H} + {n} * {ROW_H} + {FOOT_H})", fp=0, visible=VIS)
    s.content = [head, *state_labels(p, "tickets"), tb, card]
    s.overlays = overlays(p)
    return s


# ------------------------------------------------------------------ scrKnowledge
def knowledge():
    p = "kb"
    s = ItScreen("scrKnowledge", p, on_visible())
    vis_list = f"{VIS} && IsBlank(varArticle)"
    vis_art = f"{VIS} && !IsBlank(varArticle)"
    head = page_head(p, "Knowledge base", "Self-service guides for common issues.", ac="AC-ITH-35.1")
    head.props["Visible"] = vis_list
    search = textinput(f"{p}Search2", default="varKQ", hint="Search articles", h=CTRL, accessible="Search articles", w=280, fp=0, onchange=f"Set(varKQ, {p}Search2.Text) // AC-ITH-35.3")
    search.props.update({"Fill": "ColorSurface", "BorderColor": "ColorBorder", "BorderThickness": 1, "PaddingLeft": 12, "DelayOutput": "true", "FocusedBorderColor": "ColorPrimary",
                         "FocusedBorderThickness": 2, "RadiusBottomLeft": CTRL_R, "RadiusBottomRight": CTRL_R, "RadiusTopLeft": CTRL_R, "RadiusTopRight": CTRL_R, "Size": BODY_PT,
                         "AlignInContainer": "AlignInContainer.Center"})
    chips = []
    for i in range(9):
        txt = '"All"' if i == 0 else f"Index(colArticleCats, {i}).Value"
        val = '""' if i == 0 else f"Index(colArticleCats, {i}).Value"
        on = f"varKC = {val}"
        c = button(f"{p}Chip{i}", "=" + txt, f"Set(varKC, {val}) // AC-ITH-35.4", "secondary", w=f"Len({txt}) * 8 + 28", h=29, size=BODY_PT, radius=14, weight="FontWeight.Normal",
                   fill=f"If({on}, ColorPrimaryTint, ColorSurface)", color=f"If({on}, ColorAccentText, ColorText)", visible="true" if i == 0 else f"CountRows(colArticleCats) >= {i}",
                   fp=0, align_in="AlignInContainer.Center")
        c.props["BorderColor"] = f"If({on}, ColorPrimaryTintBorder, ColorDivider)"
        c.props["HoverFill"] = f"If({on}, ColorPrimaryTint, ColorHover)"
        chips.append(c)
    tb = hrow(f"{p}Tb", [search] + chips, 40, 6, 0, vis_list, align="Center")
    tb.children[0].props["FillPortions"] = 0
    # card grid: 4 across (min 260, gap 14) as a wrapping gallery
    card_cells = [box(f"{p}CardIn", [lbl(f"{p}CardCat", "=ThisItem.ArticleCategory", BODY_PT, False, "ColorTextMuted", h=BODY_LH),
                                     lbl(f"{p}CardTitle", "=ThisItem.Title", H3_PT, True, h=42, wrap=True),
                                     label(f"{p}CardDesc", "=ThisItem.ArticleSummary", size=BODY_PT, color="ColorTextMuted", h=42)], "Vertical", 4, fp=1, h=None)]
    card_cells[0].props["LayoutAlignItems"] = "LayoutAlignItems.Stretch"
    row = box(f"{p}GalRow", card_cells, "Horizontal", 0, h="Parent.TemplateHeight", w="Parent.TemplateWidth", fill="ColorSurface", pad=16, border=True, radius=CARD_R, border_color="ColorDivider", min0=False)
    gal = Node(f"{p}Grid", "Gallery@2.15.0", {"BorderColor": "ColorTransparent", "Height": "Parent.Height", "Items": "FilteredArticles // AC-ITH-35.2", "TemplateSize": 160, "TemplatePadding": 14,
                                              "Width": "Parent.Width", "WrapCount": 4, "OnSelect": "Set(varArticle, ThisItem) // AC-ITH-36.1"}, [row], variant="BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0")
    grid_n = "CountRows(FilteredArticles)"
    grid = Node(f"{p}GridWrap", "GroupContainer@1.5.0", {"DropShadow": "DropShadow.None", "FillPortions": 0, "Height": f"RoundUp({grid_n} / 4, 0) * 174", "LayoutMaxHeight": "", "LayoutMaxWidth": "",
                                                       "Visible": f"{vis_list} && {grid_n} > 0"}, [gal], variant="ManualLayout")
    empty = empty_label(f"{p}Empty", '="No articles match """ & varKQ & """."', f"{vis_list} && {grid_n} = 0", h=66)
    # article view (AC-ITH-36)
    back = button(f"{p}Back", "Back to articles", "Set(varArticle, Blank()) // AC-ITH-36.2", "tab", w=140, h=BTN_H, size=BODY_PT, color="ColorTextMuted", weight="FontWeight.Semibold", visible=vis_art,
                  fp=0, hover_fill="ColorHover", radius=CTRL_R)
    back.props["Align"] = "Align.Left"
    a_title = label(f"{p}ATitle", "=varArticle.Title", size=16.5, bold=True, h=33, role="Heading1", visible=vis_art, fp=0, ac="AC-ITH-36.1")
    a_sub = label(f"{p}ASub", '=varArticle.ArticleCategory & " · " & varArticle.ArticleSummary', size=BODY_PT, color="ColorTextMuted", h=BODY_LH, visible=vis_art, fp=0)
    steps_n = "CountRows(ArticleSteps)"
    step_cells = [lbl(f"{p}StepN", '=ThisItem.N & "."', BODY_PT, True, "ColorAccentText", w=28, fp=0), label(f"{p}StepT", "=ThisItem.Text", size=BODY_PT, h=42, fp=1, valign="Middle")]
    steps = table(f"{p}Steps", "ArticleSteps", step_cells, f"{steps_n} * 48", tpl=48, visible=vis_art, ac="AC-ITH-36.1", row_fill="ColorSurface", row_pad=16, row_gap=8)
    steps_card = card_shell(f"{p}StepsCard", [steps], h=f"{steps_n} * 48", fp=0, visible=vis_art)
    still = card_shell(f"{p}Still", [hrow(f"{p}StillIn", [lbl(f"{p}StillT", "Still stuck?", BODY_PT, False, fp=1), button(f"{p}StillB", "Create ticket",
                      "Set(varPrefill, varArticle.Title); " + OPEN_FORM_NEW + " // AC-ITH-36.3", "primary", w=133, h=BTN_H, size=BODY_PT, radius=CTRL_R, weight="FontWeight.Semibold",
                      align_in="AlignInContainer.Center", fp=0)], 70, 10, 0, pad_x=16, align="Center")], h=70, fp=0, visible=vis_art)
    s.content = [head, *state_labels(p, "articles"), tb, grid, empty, back, a_title, a_sub, steps_card, still]
    s.overlays = overlays(p)
    return s


# ------------------------------------------------------------------ scrSettings
def settings():
    p = "st"
    s = ItScreen("scrSettings", p, on_visible())
    head = page_head(p, "Settings", "Reference information about the helpdesk.", ac="AC-ITH-37.1")
    user_card = card_shell(f"{p}User", [lbl(f"{p}UserT", "Current user", H3_PT, True, h=BODY_LH, role="Heading2"),
                                        hrow(f"{p}UserRow", [avatar(f"{p}UserAv", "=Initials(User().FullName)", 30, SMALL_PT, fill="ColorPrimaryTint", color="ColorAccentText", accessible='""'),
                                                             box(f"{p}UserTx", [lbl(f"{p}UserN", "=User().FullName", BODY_PT, True, h=BODY_LH), lbl(f"{p}UserE", "=User().Email", BODY_PT, False,
                                                                                                                            "ColorTextMuted", h=BODY_LH)], "Vertical", 0, fp=1)], 44, 10, 0, align="Center"),
                                        lbl(f"{p}UserR", '="Role: " & MyRole', BODY_PT, False, "ColorTextMuted", h=BODY_LH, ac="AC-ITH-37.2")], h=150, fp=1)
    user_card.props.update({"PaddingLeft": 16, "PaddingRight": 16, "PaddingTop": 16, "PaddingBottom": 16, "LayoutGap": 8})
    cat_chips = []
    for i in range(6):
        c = pill(f"{p}Cat{i}", f"=Index(colCategoryOpt, {i + 1}).Value", "ColorSurface", "ColorText", f"Len(Index(colCategoryOpt, {i + 1}).Value) * 8 + 28", h=29, size=BODY_PT, visible=f"CountRows(colCategoryOpt) >= {i + 1}")
        c.props["BorderColor"], c.props["BorderThickness"] = "ColorDivider", 1
        c.props["RadiusTopLeft"] = c.props["RadiusTopRight"] = c.props["RadiusBottomLeft"] = c.props["RadiusBottomRight"] = 14
        cat_chips.append(c)
    cat_card = card_shell(f"{p}Cats", [lbl(f"{p}CatsT", "Ticket categories", H3_PT, True, h=BODY_LH, role="Heading2"),
                                       hrow(f"{p}CatsRow", cat_chips, 29, 6, 0, align="Center")], h=150, fp=1)
    cat_card.props.update({"PaddingLeft": 16, "PaddingRight": 16, "PaddingTop": 16, "PaddingBottom": 16, "LayoutGap": 10})
    row1 = hrow(f"{p}Row1", [user_card, cat_card], 150, GAP, 0, VIS)

    def defs(key, head_text, items, fill_fmt, txt_fmt, ac):
        n = f"CountRows({items})"
        cells = [pill(f"{p}{key}B", "=ThisItem.Title", fill_fmt.format(v="ThisItem.Title"), txt_fmt.format(v="ThisItem.Title"), 96),
                 label(f"{p}{key}D", f'=Coalesce(ThisItem.{ "PriorityDefinition" if key == "Pr" else "StatusDefinition"}, "")', size=BODY_PT, color="ColorTextMuted", h=42, fp=1, valign="Middle")]
        t = table(f"{p}{key}Tbl", items, cells, f"{n} * 48", tpl=48, visible=f"{n} > 0", ac=ac, row_fill="ColorSurface", row_pad=0, row_gap=10)
        c = card_shell(f"{p}{key}Card", [lbl(f"{p}{key}T", head_text, H3_PT, True, h=BODY_LH, role="Heading2"), t], h=f"16 + {BODY_LH} + 8 + {n} * 48 + 16", fp=1)
        c.props.update({"PaddingLeft": 16, "PaddingRight": 16, "PaddingTop": 16, "PaddingBottom": 16, "LayoutGap": 8})
        return c

    row2 = hrow(f"{p}Row2", [defs("Pr", "Priority definitions", "colPriority", PR_FILL, PR_TXT, "AC-ITH-37.4"), defs("Sd", "Status definitions", "colStatus", ST_FILL, ST_TXT, "AC-ITH-37.4")],
                f"16 + {BODY_LH} + 8 + Max(CountRows(colPriority), CountRows(colStatus)) * 48 + 16", GAP, 0, VIS)
    s.content = [head, *state_labels(p, "settings"), row1, row2]
    s.overlays = overlays(p)
    return s


# ------------------------------------------------------------------ the overlay set: drawer, form, confirmation (on every screen)
def overlays(p):
    return drawer(p) + form(p) + confirm(p)


def tdrop(name, items, default, onchange, label_text, w, x=None, y=None, fp=None, display="If(CanChange, DisplayMode.Edit, DisplayMode.View)", ac=None, visible=None):
    d = dropdown(name, items)
    d.props.update({"AccessibleLabel": f'"{label_text}"', "Default": default, "OnChange": onchange + (f" // {ac}" if ac else ""), "DisplayMode": display})
    for k, v in (("Width", w), ("X", x), ("Y", y), ("FillPortions", fp)):
        if v is not None:
            d.props[k] = v
    if visible is not None:
        d.props["Visible"] = visible  # an overlay control is shown by its overlay's variable, never always
    return d


def drawer(p):
    X = f"Parent.Width - {DRAWER_W}"
    shown = "varDrawer"
    t = "varTicket"
    ov = label(f"{p}DrwOv", '=""', size=BODY_PT, h="Parent.Height", w="Parent.Width", x=0, y=0, fill="ColorOverlay", visible=shown)
    ov.props["OnSelect"] = 'Set(varDrawer, false) // AC-ITH-24.1'
    ov.props["AccessibleLabel"] = None
    ov.props.pop("AccessibleLabel")
    # header rows
    top = hrow(f"{p}DrwTop", [lbl(f"{p}DrwId", f"={t}.Code", BODY_PT, True, "ColorAccentText", fp=1, h=32, valign="Middle", ac="AC-ITH-24.2"),
                              button(f"{p}DrwClose", "Close panel", "Set(varDrawer, false) // AC-ITH-24.1", "secondary", w=104, h=32, size=SMALL_PT, radius=6, fill="ColorSurface", fp=0,
                                     weight="FontWeight.Normal", align_in="AlignInContainer.Center")], 32, 8, 0, align="Center")
    subj = label(f"{p}DrwSubj", f'=If(Len({t}.Title) > 70, Left({t}.Title, 69) & "…", {t}.Title)', size=15.75, bold=True, h=64, fp=0, role="Heading2", ac="AC-ITH-24.2")
    subj.props["Wrap"] = "true"
    badges = hrow(f"{p}DrwBadges", [st_pill(f"{p}DrwSt", f"{t}.TicketStatus", 96), pr_pill(f"{p}DrwPr", f"{t}.Priority", 76),
                                    box(f"{p}DrwBSp", [], "Horizontal", 0, fp=1)], 24, 6, 0, align="Center")
    act_btns = hrow(f"{p}DrwActs", [
        button(f"{p}DrwEdit", "Edit", OPEN_FORM_EDIT, "secondary", w=70, h=BTN_H, size=BODY_PT, radius=CTRL_R, weight="FontWeight.Semibold", fill="ColorSurface", fp=0, visible="CanEdit",
               align_in="AlignInContainer.Center"),
        button(f"{p}DrwResolve", "Resolve", change_field("StatusChanged", "TicketStatus", '"Resolved"', "status to Resolved", 'Notify(' + f'{t}.Code & " marked Resolved", NotificationType.Success)') + " // AC-ITH-29.1",
               "secondary", w=90, h=BTN_H, size=BODY_PT, radius=CTRL_R, weight="FontWeight.Semibold", fill="ColorSurface", fp=0,
               visible=f"CanChange && !{t}.IsFinal", align_in="AlignInContainer.Center"),
        button(f"{p}DrwCloseT", "Close ticket", 'Set(varModal, "close") // AC-ITH-29.2', "secondary", w=120, h=BTN_H, size=BODY_PT, radius=CTRL_R, weight="FontWeight.Semibold", fill="ColorSurface", fp=0,
               visible=f'CanChange && {t}.TicketStatus <> "Closed"', align_in="AlignInContainer.Center")], BTN_H, 8, 0, "CanEdit || CanChange", align="Center")
    # detail grid (AC-ITH-24.3, AC-ITH-25)
    def cap(name, text):
        return lbl(name, text, BADGE_PT, False, "ColorTextMuted", h=19)

    st_dd = tdrop(f"{p}DrwStDd", "colStatusOpt", f"LookUp(colStatusOpt, Value = {t}.TicketStatus)",
                  change_field_expr("StatusChanged", "TicketStatus", f"{p}DrwStDd.Selected.Value", "status to ", "AC-ITH-25.1"), "Status", None, fp=1)
    pr_dd = tdrop(f"{p}DrwPrDd", "colPriorityOpt", f"LookUp(colPriorityOpt, Value = {t}.Priority)",
                  change_field_expr("PriorityChanged", "TicketPriority", f"{p}DrwPrDd.Selected.Value", "priority to ", "AC-ITH-25.1"), "Priority", None, fp=1)
    as_dd = tdrop(f"{p}DrwAsDd", "colAssignOpt", f"LookUp(colAssignOpt, Value = Coalesce({t}.AssignedToName, \"Unassigned\"))",
                  assign_expr(f"{p}DrwAsDd"), "Assigned technician", None, fp=1)
    grid1 = hrow(f"{p}DrwG1", [box(f"{p}DrwG1a", [cap(f"{p}DrwG1aC", "Status"), st_dd], "Vertical", 4, fp=1), box(f"{p}DrwG1b", [cap(f"{p}DrwG1bC", "Priority"), pr_dd], "Vertical", 4, fp=1)], 58, 18, 0)
    grid2 = hrow(f"{p}DrwG2", [box(f"{p}DrwG2a", [cap(f"{p}DrwG2aC", "Assigned technician"), as_dd], "Vertical", 4, fp=1),
                               box(f"{p}DrwG2b", [cap(f"{p}DrwG2bC", "Category"), lbl(f"{p}DrwCat", f"={t}.Category", BODY_PT, False, h=34, valign="Middle")], "Vertical", 4, fp=1)], 58, 18, 0)
    grid3 = hrow(f"{p}DrwG3", [box(f"{p}DrwG3a", [cap(f"{p}DrwG3aC", "Requester"), lbl(f"{p}DrwReq", f"={t}.RequesterName", BODY_PT, False, h=BODY_LH),
                                                  lbl(f"{p}DrwReqE", f"={t}.RequesterEmail", BODY_PT, False, "ColorTextMuted", h=BODY_LH)], "Vertical", 4, fp=1),
                               box(f"{p}DrwG3b", [cap(f"{p}DrwG3bC", "Created"), lbl(f"{p}DrwCr", f"={t}.CreatedFull", BODY_PT, False, h=BODY_LH), cap(f"{p}DrwG3cC", "Last updated"),
                                                  lbl(f"{p}DrwUp", f"={t}.ModifiedFull", BODY_PT, False, h=BODY_LH)], "Vertical", 2, fp=1)], 90, 18, 0)
    desc_lines = f"(RoundUp(Len({t}.Details) / 70, 0) + CountRows(Split({t}.Details, Char(10))) - 1)"
    desc = box(f"{p}DrwDesc", [lbl(f"{p}DrwDescH", "Description", H3_PT, True, h=BODY_LH, role="Heading2"),
                               label(f"{p}DrwDescT", f"={t}.Details", size=BODY_PT, h=f"Max(1, {desc_lines}) * 21", ac="AC-ITH-24.4")], "Vertical", 8, h=f"29 + Max(1, {desc_lines}) * 21", fp=0)
    desc.children[1].props["Wrap"] = "true"
    att_n = "CountRows(colAttach)"
    att = box(f"{p}DrwAtt", [lbl(f"{p}DrwAttH", "Attachments", H3_PT, True, h=BODY_LH, role="Heading2"),
                             lbl(f"{p}DrwAttNone", "No attachments.", BODY_PT, False, "ColorTextMuted", visible=f"{att_n} = 0", h=BODY_LH),
                             table(f"{p}DrwAttTbl", "colAttach", [lbl(f"{p}DrwAttN", "=ThisItem.Name", BODY_PT, False, fp=1)], f"{att_n} * 40", tpl=40, visible=f"{att_n} > 0", ac="AC-ITH-23.3",
                                   row_fill="ColorSurface", row_pad=12, row_gap=8)], "Vertical", 8, h=f"29 + If({att_n} = 0, 21, {att_n} * 40)", fp=0)
    cm_n = "CountRows(colComments)"
    cm_cells = [box(f"{p}DrwCmIn", [hrow(f"{p}DrwCmH", [lbl(f"{p}DrwCmA", "=ThisItem.Author", BODY_PT, True, h=BODY_LH, fp=0, w=150), lbl(f"{p}DrwCmT", "=ThisItem.AtText", SMALL_PT, False, "ColorTextMuted", h=BODY_LH, fp=1)],
                                    BODY_LH, 8, 0, align="Center"), ro_text(f"{p}DrwCmB", "ThisItem.Body", h=63)], "Vertical", 0, fp=1)]
    cm = box(f"{p}DrwCm", [label(f"{p}DrwCmHd", f'="Comments (" & {cm_n} & ")"', size=H3_PT, bold=True, h=BODY_LH, role="Heading2", ac="AC-ITH-27.1"),
                           lbl(f"{p}DrwCmNone", "No comments yet.", BODY_PT, False, "ColorTextMuted", visible=f"{cm_n} = 0", h=BODY_LH),
                           table(f"{p}DrwCmTbl", "colComments", cm_cells, f"{cm_n} * 100", tpl=100, visible=f"{cm_n} > 0", ac="AC-ITH-27.1", row_fill="ColorSurface", row_pad=0, row_gap=8)],
             "Vertical", 8, h=f"29 + If({cm_n} = 0, 21, {cm_n} * 100)", fp=0)
    new_cm = textinput(f"{p}DrwNew", default='""', hint="Write a comment", h=76, multiline=True, accessible="Comment", fp=0)
    new_cm.props.update({"BorderColor": "ColorBorder", "BorderThickness": 1, "Fill": "ColorSurface", "Size": BODY_PT, "PaddingLeft": 10, "RadiusBottomLeft": CTRL_R, "RadiusBottomRight": CTRL_R,
                         "RadiusTopLeft": CTRL_R, "RadiusTopRight": CTRL_R, "FocusedBorderColor": "ColorPrimary", "FocusedBorderThickness": 2})
    add_cm = button(f"{p}DrwAdd", "Add comment", add_comment_expr(f"{p}DrwNew"), "primary", w=130, h=BTN_H, size=BODY_PT, radius=CTRL_R, weight="FontWeight.Semibold", fp=0, align_in="AlignInContainer.End")
    add_row = hrow(f"{p}DrwAddRow", [box(f"{p}DrwAddSp", [], "Horizontal", 0, fp=1), add_cm], BTN_H, 8, 0, align="Center")
    ac_n = "CountRows(colTActivity)"
    ac_cells = [svg_bar(f"{p}DrwActDot", "0", 8, 8, "HexAccentText", "HexAccentText", align_in="AlignInContainer.Start"),
                box(f"{p}DrwActTx", [lbl(f"{p}DrwActA", "=ThisItem.Text", BODY_PT, False, h=BODY_LH), lbl(f"{p}DrwActB", "=ThisItem.AtText", SMALL_PT, False, "ColorTextMuted", h=SMALL_LH)], "Vertical", 0, fp=1)]
    ac_cells[0].props.update({"Width": 8, "Y": 0})
    act_sec = box(f"{p}DrwAct", [label(f"{p}DrwActHd", "Activity", size=H3_PT, bold=True, h=BODY_LH, role="Heading2", ac="AC-ITH-28.1"),
                                 table(f"{p}DrwActTbl", "colTActivity", ac_cells, f"Min({ac_n} * 50, 500)", tpl=50, visible=f"{ac_n} > 0", ac="AC-ITH-28.1", row_fill="ColorSurface", row_pad=0, row_gap=10)],
                  "Vertical", 8, h=f"29 + If({ac_n} = 0, 21, Min({ac_n} * 50, 500))", fp=0)
    body_kids = [top, subj, badges, act_btns, grid1, grid2, grid3, desc, att, cm, new_cm, add_row, act_sec]
    drw = box(f"{p}DrwBody", body_kids, "Vertical", 12, h="Parent.Height", w=DRAWER_W, y=0, fill="ColorSurface", pad=20, border=True, scroll=True, min0=False, border_color="ColorDivider")
    drw.props.update({"X": X, "Visible": shown, "DropShadow": "DropShadow.Bold"})
    return [ov, drw]


def activity_title(text):
    return f'User().FullName & " {text}'


def change_field_expr(event, col, value_expr, phrase, ac):
    """OnChange of a drawer dropdown (status, priority): saves at once, logs, reloads (AC-ITH-25.2, 25.3)."""
    return change_field(event, col, value_expr, phrase, "Notify(" + (f'varTicket.Code & " marked " & {value_expr}' if col == "TicketStatus" else '"Ticket updated"') + ", NotificationType.Success)", ac=ac, guard=True)


def change_field(event, col, value_expr, phrase, notify, ac=None, guard=False):
    t = "varTicket"
    cur = {"TicketStatus": f"{t}.TicketStatus", "TicketPriority": f"{t}.Priority"}[col]
    ev = f'If({value_expr} = "Resolved", "Resolved", "{event}")' if col == "TicketStatus" else f'"{event}"'
    write_t = (f'Collect(MockTouch, {{ID: {t}.ID}})' if MOCK else f'Patch(ITH_Ticket, LookUp(ITH_Ticket, ID = {t}.ID), {{{col}: {value_expr}}})')
    if MOCK:
        write_t = f'Patch(MockTicketLive, LookUp(MockTicketLive, ID = {t}.ID), {{{col}: {value_expr}}})'
    act = write_activity("%EV%", f'User().FullName & " changed {phrase}" & {value_expr}', value_expr)
    if not MOCK:
        act = act.replace('{Value: "%EV%"}', "{Value: " + ev + "}")
    else:
        act = act.replace('"%EV%"', ev)
    body = (f'IfError(\n    {write_t};\n    {act};\n    {RELOAD.replace(NL, NL + "    ")};\n    Set(varTicket, LookUp(colTickets, ID = {t}.ID));\n    {notify};\n    true,\n'
            f'    Notify(If(FirstError.Kind = ErrorKind.EditPermissions, "You don\'t have access to change this ticket.", "The ticket was not changed. " & FirstError.Message), NotificationType.Error))')
    if guard:
        return f"If({value_expr} <> {cur},\n  {body})" + (f" // {ac}" if ac else "")
    return body


def assign_expr(ctl):
    t = "varTicket"
    val = f"{ctl}.Selected.Value"
    name = f'If({val} = "Unassigned", "", {val})'
    email = f'Coalesce(LookUp(colTechnician, Title = {name}).TechnicianEmail, "")'
    write_t = (f'Patch(MockTicketLive, LookUp(MockTicketLive, ID = {t}.ID), {{AssignedToName: {name}, AssignedToEmail: {email}}})' if MOCK else
               f'Patch(ITH_Ticket, LookUp(ITH_Ticket, ID = {t}.ID), {{AssignedToName: {name}, AssignedToEmail: {email}}})')
    act = write_activity("AssigneeChanged", f'User().FullName & " changed assignee to " & {val}', name)
    if not MOCK:
        pass
    return (f'If({val} <> Coalesce({t}.AssignedToName, "Unassigned") && !(IsBlank({t}.AssignedToName) && {val} = "Unassigned"),\n  IfError(\n    {write_t};\n    {act};\n'
            f'    {RELOAD.replace(NL, NL + "    ")};\n    Set(varTicket, LookUp(colTickets, ID = {t}.ID));\n    Notify("Ticket updated", NotificationType.Success);\n    true,\n'
            f'    Notify(If(FirstError.Kind = ErrorKind.EditPermissions, "You don\'t have access to change this ticket.", "The ticket was not changed. " & FirstError.Message), NotificationType.Error))) // AC-ITH-25.1')


def add_comment_expr(box_):
    t = "varTicket"
    txt = f"Trim({box_}.Text)"
    write_c = (f'Collect(MockCommentLive, {{ID: Coalesce(Max(MockCommentLive, ID), 100) + 1, TicketId: {t}.ID, AuthorName: User().FullName, CommentText: {txt}, Created: Now()}})' if MOCK else
               f'Patch(ITH_TicketComment, Defaults(ITH_TicketComment), {{Title: Left({txt}, 60), TicketId: {t}.ID, TicketTitle: {t}.Title, CommentText: {txt}, AuthorName: User().FullName, AuthorEmail: User().Email}})')
    act = write_activity("Comment", 'User().FullName & " added a comment"', "User().FullName")
    return (f'If(IsBlank({txt}),\n  Notify("Write a comment before adding it.", NotificationType.Error), // AC-ITH-27.3\n  IfError(\n    {write_c};\n    {act};\n    Reset({box_});\n'
            f'    {LOAD_DRAWER.replace(NL, NL + "    ")};\n    {RELOAD.replace(NL, NL + "    ")};\n    Notify("Comment added", NotificationType.Success);\n    true,\n'
            f'    Notify("The comment was not added. " & FirstError.Message, NotificationType.Error))) // AC-ITH-27.4')


# ------------------------------------------------------------------ form modal (AC-ITH-20 to 22, 26)
def form(p):
    shown = 'varModal = "form"'
    py = "pnForm.Y"
    e1, e2, e3 = "If(varErrSubject, 18, 0)", "If(varErrDesc, 18, 0)", "If(varErrEmail, 18, 0)"
    W = MODAL_W
    iw, half = W - 40, (W - 40 - 12) // 2
    edit = 'varFormMode = "edit"'
    t = "varTicket"

    def y(off):
        return f"{py} + {off}"

    def x(off=20):
        return f"pnForm.X + {off}"

    def cap(name, text, yy, ww=iw, xx=None, vis=shown):
        return lbl(name, text, BODY_PT, True, h=BODY_LH, w=ww, x=xx or x(), y=yy, visible=vis)

    def tin(name, default, hint, h, yy, access, ww=iw, xx=None, multiline=False, err=None, ac=None):
        n = textinput(name, default=default, hint=hint, h=h, multiline=multiline, accessible=access, x=xx or x(), y=yy, w=ww, visible=shown, ac=ac)
        n.props.update({"BorderColor": f"If({err}, ColorError, ColorBorder)" if err else "ColorBorder", "Fill": "ColorSurface", "Size": BODY_PT, "PaddingLeft": 10, "FocusedBorderColor": "ColorPrimary",
                        "FocusedBorderThickness": 2, "RadiusBottomLeft": CTRL_R, "RadiusBottomRight": CTRL_R, "RadiusTopLeft": CTRL_R, "RadiusTopRight": CTRL_R})
        return n

    def errl(name, text, yy, vis, ww=iw, xx=None, ac=None):
        n = label(name, text, size=SMALL_PT, color="ColorError", h=18, w=ww, x=xx or x(), y=yy, visible=vis, ac=ac)
        n.props["Live"] = "Live.Polite"
        return n

    key = "varFormKey"
    subject = tin("fmSubject", f'If({edit}, {t}.Title, Coalesce(varPrefill, ""))', "Short summary of the issue", CTRL, y(f"{20 + 32 + 12 + 25}"), "Ticket subject", err="varErrSubject", ac="AC-ITH-20.2")
    descr = tin("fmDesc", f'If({edit}, {t}.Details, "")', "What happened, and what did you expect?", 96, y(f"160 + {e1}"), "Description", multiline=True, err="varErrDesc", ac="AC-ITH-20.2")
    oy = f"268 + {e1} + {e2}"                         # category/priority row
    cat_dd = tdrop("fmCat", "colCategoryOpt", f'If({edit}, LookUp(colCategoryOpt, Value = {t}.Category), LookUp(colCategoryOpt, Value = "Software"))', "x", "Category", half, x=x(), y=y(f"{oy} + 25"), display="DisplayMode.Edit", visible=shown)
    pri_dd = tdrop("fmPri", "colPriorityOpt", f'If({edit}, LookUp(colPriorityOpt, Value = {t}.Priority), LookUp(colPriorityOpt, Value = "Medium"))', "x", "Priority", half, x=x(20 + half + 12), y=y(f"{oy} + 25"),
                   display="DisplayMode.Edit", visible=shown)
    for d in (cat_dd, pri_dd):
        d.props.pop("OnChange", None)
    ry = f"{oy} + 71"                                 # requester row
    req_n = tin("fmReqName", f'If({edit}, {t}.RequesterName, User().FullName)', "", CTRL, y(f"{ry} + 25"), "Requester name", ww=half)
    req_e = tin("fmReqEmail", f'If({edit}, {t}.RequesterEmail, User().Email)', "", CTRL, y(f"{ry} + 25"), "Requester email", ww=half, xx=x(20 + half + 12), err="varErrEmail", ac="AC-ITH-20.4")
    for r_ in (req_n, req_e):
        r_.props["DisplayMode"] = "If(IsStaff, DisplayMode.Edit, DisplayMode.View)"
    ay = f"{ry} + 71 + {e3}"
    as_dd = tdrop("fmAssign", "colAssignOpt", f'If({edit}, LookUp(colAssignOpt, Value = Coalesce({t}.AssignedToName, "Unassigned")), First(colAssignOpt))', "x", "Assign to (optional)", iw, x=x(), y=y(f"{ay} + 25"),
                  display="DisplayMode.Edit", visible=shown)
    as_dd.props.pop("OnChange", None)
    by = f"{ay} + 71"
    height = f"{by} + {BTN_H} + 20"
    cancel = button("fmCancel", "Cancel", 'Set(varModal, ""); Set(varPrefill, "") // AC-ITH-20.6', "secondary", w=80, h=BTN_H, x=x(W - 20 - 130 - 8 - 80), y=y(f"{by}"), visible=shown, size=BODY_PT, radius=CTRL_R,
                    weight="FontWeight.Semibold", fill="ColorSurface")
    submit = button("fmSave", f'=If({edit}, "Save changes", "Create ticket")', save_ticket_expr(), "primary", w=130, h=BTN_H, x=x(W - 20 - 130), y=y(f"{by}"), visible=shown, size=BODY_PT, radius=CTRL_R,
                    weight="FontWeight.Semibold", display="If(varSaving, DisplayMode.Disabled, DisplayMode.Edit)")
    ov = label(f"{p}FmOv", '=""', size=BODY_PT, h="Parent.Height", w="Parent.Width", x=0, y=0, fill="ColorOverlay", visible=shown)
    ov.props["OnSelect"] = 'Set(varModal, "") // AC-ITH-20.6'
    nodes = [ov,
             panel("pnForm", f"(Parent.Width - {W}) / 2", f"Max(12, (Parent.Height - Self.Height) / 2)", W, height, fill="ColorSurface", border_color="ColorDivider", radius=12, shadow="Bold", visible=shown),
             label("fmTitle", '=If(varFormMode = "edit", "Edit " & varTicket.Code, "Create ticket")', size=H3_PT + 1.5, bold=True, h=32, w=iw - 44, x=x(), y=y(20), visible=shown, role="Heading2", valign="Middle"),
             *icon_button("fmX", "x", "Close", x(W - 20 - 34), y(19), 'Set(varModal, ""); Set(varPrefill, "")', visible=shown),
             cap("fmSubjectCap", "Ticket subject *", y(f"{20 + 32 + 12}")), subject,
             errl("fmSubjectErr", "Enter a subject.", y("125"), "varErrSubject", ac="AC-ITH-22.1"),
             cap("fmDescCap", "Description *", y(f"135 + {e1}")), descr,
             errl("fmDescErr", "Describe the issue.", y(f"160 + {e1} + 96 + 2"), "varErrDesc", ac="AC-ITH-22.2"),
             cap("fmCatCap", "Category", y(oy), ww=half), cat_dd, cap("fmPriCap", "Priority", y(oy), ww=half, xx=x(20 + half + 12)), pri_dd,
             cap("fmReqNameCap", "Requester name", y(ry), ww=half), req_n, cap("fmReqEmailCap", "Requester email", y(ry), ww=half, xx=x(20 + half + 12)), req_e,
             errl("fmReqEmailErr", "Enter a valid email address.", y(f"{ry} + 25 + 34 + 2"), "varErrEmail", ww=half, xx=x(20 + half + 12), ac="AC-ITH-22.3"),
             cap("fmAssignCap", "Assign to (optional)", y(ay)), as_dd, cancel, submit]
    return nodes


def save_ticket_expr():
    t = "varTicket"
    sub, des, mail = "Trim(fmSubject.Text)", "Trim(fmDesc.Text)", "Trim(fmReqEmail.Text)"
    sets = (f'Set(varErrSubject, IsBlank({sub})); // AC-ITH-22.1\nSet(varErrDesc, IsBlank({des})); // AC-ITH-22.2\n'
            f'Set(varErrEmail, !IsBlank({mail}) && !IsMatch({mail}, "^\\S+@\\S+\\.\\S+$")); // AC-ITH-22.3')
    asg_name = 'If(fmAssign.Selected.Value = "Unassigned", "", fmAssign.Selected.Value)'
    asg_mail = f'Coalesce(LookUp(colTechnician, Title = {asg_name}).TechnicianEmail, "")'
    req_name = 'Coalesce(Trim(fmReqName.Text), User().FullName)'
    req_mail = f'Coalesce({mail}, User().Email)'
    fields = (f'Title: {sub}, TicketDescription: {des}, TicketCategory: fmCat.Selected.Value, TicketPriority: fmPri.Selected.Value, RequesterName: {req_name}, '
              f'RequesterEmail: {req_mail}, AssignedToName: {asg_name}, AssignedToEmail: {asg_mail}')
    reload = RELOAD.replace(NL, NL + "        ")
    if MOCK:
        create = (f'With({{rec: Collect(MockTicketLive, {{ID: Coalesce(Max(MockTicketLive, ID), 1000) + 1, Title: {sub}, TicketDescription: {des}, TicketCategory: fmCat.Selected.Value, '
                  f'TicketPriority: fmPri.Selected.Value, TicketStatus: "Open", RequesterName: {req_name}, RequesterEmail: {req_mail}, AssignedToName: {asg_name}, AssignedToEmail: {asg_mail}, '
                  f'Created: Now(), Modified: Now()}})}}, Set(varLast, rec));')
        edit = (f'Patch(MockTicketLive, LookUp(MockTicketLive, ID = {t}.ID), {{{fields}, Modified: Now()}});\n        '
                f'Collect(MockActivityLive, {{ID: Coalesce(Max(MockActivityLive, ID), 100) + 1, TicketId: {t}.ID, Title: User().FullName & " edited ticket details", Created: Now()}});')
    else:
        create = (f'Set(varLast, Patch(ITH_Ticket, Defaults(ITH_Ticket), {{{fields}, TicketStatus: "Open"}}));\n        '
                  f'Patch(ITH_TicketActivity, Defaults(ITH_TicketActivity), {{Title: {req_name} & " created the ticket", TicketId: varLast.ID, TicketTitle: varLast.Title, EventType: {{Value: "Created"}}, '
                  f'EventValue: "", ActorName: User().FullName, ActorEmail: User().Email}});\n        '
                  f'If(!IsBlank({asg_name}), Patch(ITH_TicketActivity, Defaults(ITH_TicketActivity), {{Title: User().FullName & " assigned the ticket to " & {asg_name}, TicketId: varLast.ID, '
                  f'TicketTitle: varLast.Title, EventType: {{Value: "Assigned"}}, EventValue: {asg_name}, ActorName: User().FullName, ActorEmail: User().Email}}));')
        edit = (f'Patch(ITH_Ticket, LookUp(ITH_Ticket, ID = {t}.ID), {{{fields}}});\n        '
                f'Patch(ITH_TicketActivity, Defaults(ITH_TicketActivity), {{Title: User().FullName & " edited ticket details", TicketId: {t}.ID, TicketTitle: {sub}, EventType: {{Value: "Edited"}}, '
                f'EventValue: "", ActorName: User().FullName, ActorEmail: User().Email}});\n        '
                f'If({asg_name} <> {t}.AssignedToName && !IsBlank({asg_name}), Patch(ITH_TicketActivity, Defaults(ITH_TicketActivity), {{Title: User().FullName & " assigned the ticket to " & {asg_name}, '
                f'TicketId: {t}.ID, TicketTitle: {sub}, EventType: {{Value: "Assigned"}}, EventValue: {asg_name}, ActorName: User().FullName, ActorEmail: User().Email}}));')
    new_created = ('Collect(MockActivityLive, {ID: Coalesce(Max(MockActivityLive, ID), 100) + 1, TicketId: varLast.ID, Title: Coalesce(Trim(fmReqName.Text), User().FullName) & " created the ticket", Created: Now()});\n        '
                   if MOCK else "")
    return (sets + '\nIf(!varErrSubject && !varErrDesc && !varErrEmail,\n  Set(varSaving, true);\n  IfError(\n    If(varFormMode = "edit",\n      ' + "\n      ".join(edit.split("\n")) + '\n      Set(varSavedMsg, varTicket.Code & " updated"),\n      '
            + create.replace("\n        ", "\n      ") + "\n      " + new_created.replace("\n        ", "\n      ") + 'Set(varSavedMsg, "HD-" & varLast.ID & " created"));\n    '
            + RELOAD.replace(NL, NL + "    ") + ';\n    If(varFormMode = "edit", Set(varTicket, LookUp(colTickets, ID = varTicket.ID)));\n    Set(varModal, "");\n    Set(varPrefill, "");\n    Set(varSaving, false);\n'
            '    Notify(varSavedMsg, NotificationType.Success); // AC-ITH-21.5\n    true,\n    Set(varSaving, false);\n'
            '    Notify(If(FirstError.Kind = ErrorKind.EditPermissions, "You don\'t have access to save this ticket.", "The ticket was not saved. " & FirstError.Message), NotificationType.Error)))  // AC-ITH-21.7')


# ------------------------------------------------------------------ close confirmation (AC-ITH-29)
def confirm(p):
    shown = 'varModal = "close"'
    W = MODAL_W
    t = "varTicket"
    ov = label(f"{p}CfOv", '=""', size=BODY_PT, h="Parent.Height", w="Parent.Width", x=0, y=0, fill="ColorOverlay", visible=shown)
    ov.props["OnSelect"] = 'Set(varModal, "") // AC-ITH-43.1'
    close_do = change_field("StatusChanged", "TicketStatus", '"Closed"', "status to Closed", f'Notify({t}.Code & " marked Closed", NotificationType.Success)') + ' // AC-ITH-29.3'
    return [ov,
            panel("pnConfirm", f"(Parent.Width - {W}) / 2", "(Parent.Height - Self.Height) / 2", W, 190, fill="ColorSurface", border_color="ColorDivider", radius=12, shadow="Bold", visible=shown),
            lbl("cfTitle", f'="Close " & {t}.Code & "?"', H3_PT + 1.5, True, h=32, w=W - 40, x="pnConfirm.X + 20", y="pnConfirm.Y + 20", visible=shown, role="Heading2", valign="Middle", ac="AC-ITH-29.2"),
            label("cfText", "Closed tickets are treated as complete. You can reopen it by changing the status.", size=BODY_PT, color="ColorTextMuted", h=42, w=W - 40, x="pnConfirm.X + 20", y="pnConfirm.Y + 58",
                  visible=shown),
            button("cfCancel", "Cancel", 'Set(varModal, "") // AC-ITH-29.3', "secondary", w=80, h=BTN_H, x=f"pnConfirm.X + {W} - 20 - 120 - 8 - 80", y="pnConfirm.Y + 190 - 20 - 37", visible=shown, size=BODY_PT,
                   radius=CTRL_R, weight="FontWeight.Semibold", fill="ColorSurface"),
            button("cfOk", "Close ticket", 'Set(varModal, ""); ' + close_do, "primary", w=120, h=BTN_H, x=f"pnConfirm.X + {W} - 20 - 120", y="pnConfirm.Y + 190 - 20 - 37", visible=shown, size=BODY_PT,
                   radius=CTRL_R, weight="FontWeight.Semibold")]


# ------------------------------------------------------------------ App.pa.yaml
def mock_data():
    """Mock<Entity> named formulas from the prototype's seed data (specs/prototype-fidelity.md P-122) plus the states the design spec lists."""
    techs = ["Alex Morgan", "Priya Nair", "Daniel Kim", "Sofia Rossi"]
    mail = lambda n_: n_.lower().replace(" ", ".") + "@example.com"
    rows = [("Unable to access VPN", "Cannot connect to the corporate VPN since this morning. Error 809 on home Wi-Fi.", "Maria Lopez", "Network", "High", "Open", "", 3),
            ("Outlook is not syncing", "Outlook has been stuck on Updating inbox since yesterday. Webmail works normally.", "Alex Morgan", "Software", "Medium", "In Progress", "Priya Nair", 20),
            ("Laptop performance issue", "Laptop freezes for several seconds when more than three apps are open.", "Tom Becker", "Hardware", "Medium", "In Progress", "Alex Morgan", 30),
            ("Request for software installation", "Need Adobe Acrobat Pro installed to edit signed vendor contracts.", "Hannah Lee", "Software", "Low", "Open", "Daniel Kim", 48),
            ("Printer connection problem", "The 3rd floor printer shows offline for everyone on the finance team.", "Raj Patel", "Hardware", "High", "On Hold", "Sofia Rossi", 52),
            ("Password reset not working", "Self-service reset sends the code but the page rejects it as expired.", "Chen Wei", "Access", "High", "Resolved", "Alex Morgan", 6),
            ("Shared mailbox access", "Please add me to the shared Accounts Payable mailbox.", "Alex Morgan", "Access", "Low", "Resolved", "Priya Nair", 3),
            ("Monitor flickering", "External monitor flickers every few minutes when docked.", "Maria Lopez", "Hardware", "Low", "Closed", "Daniel Kim", 120),
            ("Teams calls dropping", "Calls drop after about ten minutes on the office Wi-Fi.", "Tom Becker", "Network", "Critical", "In Progress", "Sofia Rossi", 8),
            ("New starter laptop setup and accounts for the analyst starting on Monday in the finance department", "Laptop and accounts needed for a new analyst starting Monday.", "Hannah Lee", "Hardware", "Medium", "Open", "Alex Morgan", 26),
            ("Cannot open shared drive", "Access denied on the Finance Reports drive since the permissions change.", "Raj Patel", "Access", "Medium", "Open", "", 70),
            ("Antivirus alert on laptop", "Defender quarantined a file in Downloads. Want to confirm it is safe.", "Alex Morgan", "Other", "Critical", "In Progress", "Daniel Kim", 7),
            ("Excel crashes on large files", "Excel closes without warning when opening the quarterly model (45 MB).", "Chen Wei", "Software", "Medium", "On Hold", "Priya Nair", 96),
            ("Request second monitor", "Requesting a second monitor to support daily reporting work.", "Alex Morgan", "Hardware", "Low", "Open", "", 150)]
    tk = []
    for i, (s_, d_, rn, c_, pr, st, asg, h) in enumerate(rows):
        tk.append(f'{{ID: {1001 + i}, Title: "{s_}", TicketDescription: "{d_}", RequesterName: "{rn}", RequesterEmail: "{mail(rn)}", TicketCategory: "{c_}", TicketPriority: "{pr}", TicketStatus: "{st}", '
                  f'AssignedToName: "{asg}", AssignedToEmail: "{mail(asg) if asg else ""}", Created: DateAdd(Now(), -{h}, TimeUnit.Hours), Modified: DateAdd(Now(), -{max(1, h // 2)}, TimeUnit.Hours)}}')
    act = []
    for i, (s_, d_, rn, c_, pr, st, asg, h) in enumerate(rows):
        act.append(f'{{ID: {10 + i}, TicketId: {1001 + i}, Title: "{rn} created the ticket", Created: DateAdd(Now(), -{h}, TimeUnit.Hours)}}')
        if asg:
            act.append(f'{{ID: {40 + i}, TicketId: {1001 + i}, Title: "Alex Morgan assigned the ticket to {asg}", Created: DateAdd(Now(), -{max(1, int(h * 0.9))}, TimeUnit.Hours)}}')
    cm = [f'{{ID: 1, TicketId: 1002, AuthorName: "Priya Nair", CommentText: "Looking into this now. I will update the ticket shortly.", Created: DateAdd(Now(), -10, TimeUnit.Hours)}}',
          f'{{ID: 2, TicketId: 1005, AuthorName: "Sofia Rossi", CommentText: "Waiting on a reply before I can continue.", Created: DateAdd(Now(), -26, TimeUnit.Hours)}}']
    arts = [("How to reset your password", "Account", "Reset a forgotten or expired password using self-service.",
             "Go to the sign-in page and select Forgot password.\" & Char(10) & \"Enter your work email and complete the verification code.\" & Char(10) & \"Choose a new password of at least 12 characters."),
            ("Troubleshooting VPN connectivity", "Network", "Fix the most common VPN connection errors.",
             "Check that you have an internet connection without the VPN.\" & Char(10) & \"Quit the VPN client fully and reopen it.\" & Char(10) & \"If error 809 persists, create a ticket and include the error text."),
            ("Setting up Outlook", "Email", "Add your work mailbox to Outlook on desktop or mobile.", "Open Outlook and select Add account.\" & Char(10) & \"Enter your work email and approve the sign-in prompt."),
            ("Requesting software access", "Software", "How to request licensed software and get it approved.", "Check the Software Center first.\" & Char(10) & \"Create a ticket in the Software category."),
            ("Connecting to office Wi-Fi", "Network", "Join the secure office network on a new device.", "Select the staff network from the Wi-Fi list.\" & Char(10) & \"Sign in with your work email and password."),
            ("Setting up multi-factor authentication", "Account", "Register your phone for sign-in approvals.", "Install the authenticator app from your app store.\" & Char(10) & \"Scan the QR code and enter the six-digit code.")]
    ar = [f'{{ID: {i + 1}, Title: "{t_}", ArticleCategory: "{c_}", ArticleSummary: "{s_}", ArticleSteps: "{st}", SortOrder: {i + 1}, IsActive: true}}' for i, (t_, c_, s_, st) in enumerate(arts)]
    return {"MockTicket": "Table(" + ", ".join(tk) + ")", "MockActivity": "Table(" + ", ".join(act) + ")", "MockComment": "Table(" + ", ".join(cm) + ")",
            "MockArticle": "Table(" + ", ".join(ar) + ")",
            "MockAttach": 'Table({TicketId: 1001, Name: "screenshot.png"}, {TicketId: 1005, Name: "printer-error.png"})',
            "MockCategory": "Table(" + ", ".join(f'{{ID: {i + 1}, Title: "{c_}", SortOrder: {i + 1}, IsActive: true}}' for i, c_ in enumerate(["Hardware", "Software", "Network", "Access", "Other"])) + ")",
            "MockPriority": "Table(" + ", ".join(f'{{ID: {i + 1}, Title: "{c_}", PriorityDefinition: "{d_}", SortOrder: {i + 1}, IsActive: true}}' for i, (c_, d_) in enumerate([
                ("Low", "Minor issue or question with a workaround. Target: 3 days."), ("Medium", "Affects one person's work, no workaround. Target: 1 day."),
                ("High", "Blocks a person or small team. Target: 4 hours."), ("Critical", "Business-wide outage or security risk. Target: 1 hour.")])) + ")",
            "MockStatus": "Table(" + ", ".join(f'{{ID: {i + 1}, Title: "{c_}", StatusDefinition: "{d_}", SortOrder: {i + 1}, IsFinal: {f}, IsActive: true}}' for i, (c_, d_, f) in enumerate([
                ("Open", "Submitted and waiting to be picked up.", "false"), ("In Progress", "A technician is actively working on it.", "false"),
                ("On Hold", "Waiting on the requester, a vendor, or parts.", "false"), ("Resolved", "A fix is in place and awaiting confirmation.", "true"),
                ("Closed", "Confirmed complete. No further work.", "true")])) + ")",
            "MockTechnician": "Table(" + ", ".join(f'{{ID: {i + 1}, Title: "{n_}", TechnicianEmail: "{mail(n_)}", SortOrder: {i + 1}, IsActive: true}}' for i, n_ in enumerate(techs)) + ")",
            "MockUserRole": 'Table({ID: 1, Title: "Mock user", UserEmail: User().Email, UserRole: {Value: "Technician"}, IsActive: true})'}


def app_yaml():
    named = [
        '// Rules used on more than one screen are defined once here (D5). Collections are loaded by each screen (ui-patterns section 6).',
        'AppTitle = "IT Help";',
        'SideW = If(varCollapsed, 64, 232);  // the sidebar, folded or not (AC-ITH-03.1)',
        '// The first letters of the first two words of a name, as the prototype\'s ini() does (AC-ITH-05.2)',
        'Initials(n: Text): Text = Upper(Left(n, 1) & If(IsBlank(Find(" ", n)), "", Mid(n, Find(" ", n) + 1, 1)));',
        '// How long ago, as the prototype\'s rel() words it (AC-ITH-07.3)',
        'RelTime(t: DateTime): Text = With({m: DateDiff(t, Now(), TimeUnit.Minutes)}, If(m < 1, "just now", m < 60, m & " min ago", m < 1440, Round(m / 60, 0) & " h ago", Round(m / 1440, 0) & " d ago"));',
        'MyRole = Coalesce(LookUp(colRole, Lower(UserEmail) = Lower(User().Email) && IsActive).UserRole, "Requester");  // from the role list, D-03 (AC-ITH-05.3)',
        'IsStaff = MyRole = "Technician" || MyRole = "Administrator";  // AC-ITH-40.1',
        'IsAdmin = MyRole = "Administrator";  // AC-ITH-41.1',
        'CanChange = IsStaff;  // status, priority, assignment, resolve and close (AC-ITH-25.6, AC-ITH-39.4)',
        'CanEdit = IsStaff;  // edit ticket details (AC-ITH-26.5, baseline Q-08)',
        'MyEmail = Lower(User().Email);',
        'MyOpenCount = CountRows(Filter(colTickets, Lower(RequesterEmail) = MyEmail && !IsFinal));  // AC-ITH-02.4',
        'AssignedOpenCount = CountRows(Filter(colTickets, Lower(AssignedToEmail) = MyEmail && !IsFinal));  // AC-ITH-02.4',
        'ResolvedToday = CountRows(Filter(colTickets, TicketStatus = "Resolved" && DateValue(Modified) = Today()));  // AC-ITH-11.2',
        'RecentTickets = FirstN(SortByColumns(colTickets, "ID", SortOrder.Descending), 6);  // AC-ITH-12.1',
        'MyAssigned = FirstN(Filter(SortByColumns(colTickets, "ID", SortOrder.Descending), Lower(AssignedToEmail) = MyEmail && !IsFinal), 5);  // AC-ITH-12.2',
        'RecentActivity = Filter(SortByColumns(colActivityAll, "ID", SortOrder.Descending), TicketId in colTickets.ID);  // AC-ITH-07.2 and AC-ITH-14.1, only tickets the user may see (Q-18)',
        'BaseTickets = Switch(varView, "mine", Filter(colTickets, Lower(RequesterEmail) = MyEmail), "assigned", Filter(colTickets, Lower(AssignedToEmail) = MyEmail), colTickets);  // AC-ITH-19.1',
        'FilteredTickets = Filter(BaseTickets, (IsBlank(Trim(varSearch)) || Lower(Trim(varSearch)) in Lower(Code & " " & Title)) && (varFStatus = "" || TicketStatus = varFStatus) && (varFPriority = "" || Priority = varFPriority) && (varFCategory = "" || Category = varFCategory));  // AC-ITH-16.1',
        'SortedTickets = SortByColumns(FilteredTickets, varSort, If(varDesc, SortOrder.Descending, SortOrder.Ascending));  // AC-ITH-17.1',
        'PageCount = Max(1, RoundUp(CountRows(FilteredTickets) / varPageSize, 0));  // AC-ITH-17.3',
        'PagedTickets = LastN(FirstN(SortedTickets, varPage * varPageSize), Max(0, Min(varPageSize, CountRows(SortedTickets) - (varPage - 1) * varPageSize)));  // AC-ITH-17.3',
        'FilteredArticles = Filter(SortByColumns(Filter(colArticles, IsActive), "SortOrder", SortOrder.Ascending), (varKC = "" || ArticleCategory = varKC) && (IsBlank(Trim(varKQ)) || Lower(Trim(varKQ)) in Lower(Title & " " & ArticleSummary)));  // AC-ITH-35.3',
        'ArticleSteps = If(IsBlank(varArticle), Table({N: 0, Text: ""}), ForAll(Sequence(CountRows(Split(varArticle.ArticleSteps, Char(10)))), {N: Value, Text: Index(Split(varArticle.ArticleSteps, Char(10)), Value).Result}));  // AC-ITH-36.1',
        'CsvText = "Ticket ID,Subject,Requester,Category,Priority,Status,Assigned To,Created Date,Last Updated" & Char(10) & Concat(SortedTickets, Code & "," & """" & Substitute(Title, """", """""") & """," & """" & RequesterName & """," & Category & "," & Priority & "," & TicketStatus & "," & """" & AssignedToName & """," & CreatedText & "," & ModifiedFull & Char(10));  // AC-ITH-42.1',
    ]
    if MOCK:
        named += ['MockState = "ready";  // ready, empty or error: lets a reviewer see each state until G8']
        for k, v in mock_data().items():
            named.append(f"{k} = {v};")
    tok = ith_app.tokens_text()
    role_load = ('ClearCollect(colRole, ForAll(MockUserRole, {UserEmail: UserEmail, UserRole: UserRole.Value, IsActive: IsActive}));\n' if MOCK else
                 'IfError(ClearCollect(colRole, ForAll(Filter(ITH_UserRole, UserEmail = User().Email), {UserEmail: UserEmail, UserRole: UserRole.Value, IsActive: IsActive})), Clear(colRole));\n')
    src = {"colCategory": ("MockCategory", "ITH_Category"), "colPriority": ("MockPriority", "ITH_Priority"), "colStatus": ("MockStatus", "ITH_Status"),
           "colTechnician": ("MockTechnician", "ITH_Technician"), "colArticles": ("MockArticle", "ITH_Article")}
    cols = {"colCategory": "{ID: ID, Title: Title, SortOrder: Coalesce(SortOrder, 0), IsActive: IsActive}",
            "colPriority": "{ID: ID, Title: Title, PriorityDefinition: Coalesce(PriorityDefinition, \"\"), SortOrder: Coalesce(SortOrder, 0), IsActive: IsActive}",
            "colStatus": "{ID: ID, Title: Title, StatusDefinition: Coalesce(StatusDefinition, \"\"), SortOrder: Coalesce(SortOrder, 0), IsFinal: IsFinal, IsActive: IsActive}",
            "colTechnician": "{ID: ID, Title: Title, TechnicianEmail: Coalesce(TechnicianEmail, \"\"), SortOrder: Coalesce(SortOrder, 0), IsActive: IsActive}",
            "colArticles": "{ID: ID, Title: Title, ArticleCategory: Coalesce(ArticleCategory, \"\"), ArticleSummary: Coalesce(ArticleSummary, \"\"), ArticleSteps: Coalesce(ArticleSteps, \"\"), SortOrder: Coalesce(SortOrder, 0), IsActive: IsActive}"}
    loads = ""
    for col, (mk, lst) in src.items():
        s_ = mk if MOCK else f'SortByColumns(Filter({lst}, ID > 0), "SortOrder", SortOrder.Ascending)'
        loads += f"ClearCollect({col}, ForAll({s_}, {cols[col]}));\n"
    opts = ('ClearCollect(colStatusOpt, ForAll(SortByColumns(Filter(colStatus, IsActive), "SortOrder", SortOrder.Ascending), {Value: Title}));\n'
            'ClearCollect(colPriorityOpt, ForAll(SortByColumns(Filter(colPriority, IsActive), "SortOrder", SortOrder.Ascending), {Value: Title}));\n'
            'ClearCollect(colCategoryOpt, ForAll(SortByColumns(Filter(colCategory, IsActive), "SortOrder", SortOrder.Ascending), {Value: Title}));\n'
            'ClearCollect(colAssignOpt, {Value: "Unassigned"}); // AC-ITH-31.2\nCollect(colAssignOpt, ForAll(SortByColumns(Filter(colTechnician, IsActive), "SortOrder", SortOrder.Ascending), {Value: Title}));\n'
            'ClearCollect(colFStatus, {Value: "All statuses"}); // AC-ITH-38.1\nCollect(colFStatus, colStatusOpt);\n'
            'ClearCollect(colFPriority, {Value: "All priorities"});\nCollect(colFPriority, colPriorityOpt);\n'
            'ClearCollect(colFCategory, {Value: "All categories"});\nCollect(colFCategory, colCategoryOpt);\n'
            'ClearCollect(colPageSizes, {Value: 5}, {Value: 10}, {Value: 25});\n'
            'ClearCollect(colArticleCats, Distinct(Filter(colArticles, IsActive), ArticleCategory))')
    if MOCK:
        loads = ("ClearCollect(MockTicketLive, MockTicket);\nClearCollect(MockActivityLive, MockActivity);\nClearCollect(MockCommentLive, MockComment);\n" + loads)
    on_start = (('Set(varCollapsed, false); // fx-ignore FX-DELEG the role and master-data lists hold under 500 items by design (data-model.md)\n'
                'Set(varMenu, ""); // AC-ITH-01.1 the app starts here, data comes from SharePoint lists\n' if not MOCK else 'Set(varCollapsed, false);\nSet(varMenu, "");\n') +
                'Set(varNotifRead, false);\nSet(varModal, "");\nSet(varDrawer, false);\nSet(varFormMode, "new");\nSet(varFormKey, 0);\n'
                'Set(varErrSubject, false);\nSet(varErrDesc, false);\nSet(varErrEmail, false);\nSet(varSaving, false);\nSet(varPrefill, "");\nSet(varView, "all");\nSet(varSearch, "");\n'
                'Set(varFStatus, "");\nSet(varFPriority, "");\nSet(varFCategory, "");\nSet(varSort, "ID");\nSet(varDesc, true);\nSet(varPage, 1);\nSet(varPageSize, 10);\nSet(varKQ, "");\nSet(varKC, "");\n'
                'Set(varArticle, Blank());\nSet(varTicket, Blank());\nSet(varLast, Blank());\nSet(varLinkDone, false);\nSet(varSavedMsg, "");\nSet(varLoading, false);\nSet(varLoadError, "");\nSet(varLoadReason, "");\n'
                'ClearCollect(colScheme, {Value: "Light"});\n' + role_load + loads + opts)
    text = ["App:", "  Properties:", "    Formulas: |-"]
    text += tok.rstrip("\n").split("\n")
    text += ["      " + l for l in ("\n".join(named)).split("\n")]
    text += ["    OnStart: |-"] + ["      " + ("=" + l if i == 0 else l) for i, l in enumerate(on_start.split("\n"))]
    text += ["    StartScreen: =scrOverview", "    Theme: =PowerAppsTheme"]
    return "\n".join(text) + "\n"


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    (SRC / "App.pa.yaml").write_text(app_yaml(), encoding="utf-8")
    for fn in (overview, tickets, knowledge, settings):
        sc = fn()
        sc.write(SRC)
        print("wrote", sc.name)
    old = SRC / "scrHome.pa.yaml"
    if old.exists():
        old.unlink()
        print("removed scrHome")
    (SRC / "_EditorState.pa.yaml").write_text("EditorState:\n  ScreensOrder:\n    - scrOverview\n    - scrTickets\n    - scrKnowledge\n    - scrSettings\n", encoding="utf-8")


if __name__ == "__main__":
    main()
