"""build_timesmodern_ui: generates the TimesModern canvas app (canvas/TimesModern/Src) with tools/canvas_ui.py. Project-specific.

Every number is the prototype's, measured by tools/prototype_design.py at scale 0.85 (specs/design-spec.md section 3 and 4), passed through
canvas_ui.Design. Colours are tokens (tools/mt_app.py). Layout follows docs/standards/ui-patterns.md: chrome controls placed on the screen,
one scrolling body, explicit heights, tables as galleries in fixed wrappers.

    uv run tools/build_timesmodern_ui.py            data from the lists (stage G8)
    uv run tools/build_timesmodern_ui.py --mock     data from the Mock<Entity> named formulas (stages G6 and G7)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canvas_ui import (Design, Node, Screen, avatar, badge, box, button, dropdown, hrow, label, panel, rect, side_nav, svg_bar,  # noqa: E402
                       svg_icon, table, textinput, _eq)
import mt_app  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "canvas" / "TimesModern" / "Src"
MOCK = "--mock" in sys.argv
d = Design(0.85)

# ------------------------------------------------------------------ the prototype's measurements (scaled px / points)
SIDE_W, TOP_H, ROW_H, HEAD_H, TH_H, CTRL = 197, 58, 54, 47, 35, 34
PAD = 24                      # .content padding
CONTENT_MAX = 1020            # .content max-width at the app's scale
GAP = 17                      # margin-bottom 20px between regions
CARD_R, CTRL_R = 10, 7        # .card 12px, controls 8px
NARROW = "Parent.Width < BreakpointNarrow"
NAVX = f"If({NARROW}, 0, {SIDE_W})"
SIDE_VISIBLE = f"!({NARROW}) || varMenuOpen"
GEO = {"w": SIDE_W, "pad_x": 12, "pad_y": 17, "gap": 20, "logo": 24, "logo_r": 7, "brand_pad": 7, "brand_gap": 8, "brand_pt": 10, "brand_h": 20,
       "item_h": 34, "item_gap": 2, "item_r": 7, "item_pad": 8, "icon": 15, "text_pt": 9}
NAV_ITEMS = [
    ("Dashboard", "scrDashboard", "<rect x='3' y='3' width='7' height='9' rx='1.5'/><rect x='14' y='3' width='7' height='5' rx='1.5'/>"
                                 "<rect x='14' y='12' width='7' height='9' rx='1.5'/><rect x='3' y='16' width='7' height='5' rx='1.5'/>"),
    ("Projects", "scrProjects", "<path d='M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/>"),
    ("Tasks", "scrTasks", "<path d='M9 11l3 3 7-7'/><path d='M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h15'/>"),
]
SEARCH_ICON = "<circle cx='11' cy='11' r='7'/><path d='M21 21l-4.3-4.3'/>"

PRIORITY_FILL = 'Switch(ThisItem.Priority, "High", ColorErrorFill, "Medium", ColorWarningFill, ColorNeutralFill)'
PRIORITY_TEXT = 'Switch(ThisItem.Priority, "High", ColorError, "Medium", ColorWarning, ColorNeutralText)'
PSTATUS_FILL = 'Switch(ThisItem.ProjectStatus, "Active", ColorPrimaryTint, "Completed", ColorSuccessFill, "On hold", ColorWarningFill, ColorNeutralFill)'
PSTATUS_TEXT = 'Switch(ThisItem.ProjectStatus, "Active", ColorPrimary, "Completed", ColorSuccess, "On hold", ColorWarning, ColorNeutralText)'
TSTATUS_FILL = 'Switch(ThisItem.TaskStatus, "In progress", ColorPrimaryTint, "Done", ColorSuccessFill, ColorNeutralFill)'
TSTATUS_TEXT = 'Switch(ThisItem.TaskStatus, "In progress", ColorPrimary, "Done", ColorSuccess, ColorNeutralText)'


# ------------------------------------------------------------------ data layer: collections in the shape the screens use (ui-patterns section 6)
def due_text(expr):
    return f'Text({expr}, "d mmm yyyy", "en-GB")'


LOAD_PEOPLE = ('ClearCollect(colPeople, ForAll(SortByColumns(Filter(MT_TeamMember, ID > 0), "ID", SortOrder.Ascending), '
               '{ID: ID, Name: Title, Email: Coalesce(Email, ""), Active: Active}))')
LOAD_PROJECTS = ('ClearCollect(colProjects, ForAll(SortByColumns(Filter(MT_Project, ID > 0), "ID", SortOrder.Ascending), '
                 '{ID: ID, Title: Title, Summary: Coalesce(ProjectDescription, ""), OwnerId: OwnerId, Owner: Coalesce(OwnerTitle, ""), '
                 'OwnerInit: Initials(Coalesce(OwnerTitle, "")), ProjectStatus: ProjectStatus.Value, Progress: Coalesce(Progress, 0), '
                 f'DueDate: DueDate, DueText: {due_text("DueDate")}}}))')
LOAD_TASKS = ('ClearCollect(colTasks, ForAll(SortByColumns(Filter(MT_Task, ID > 0), "ID", SortOrder.Ascending), '
              '{ID: ID, Title: Title, ProjectId: ProjectId, Project: Coalesce(ProjectTitle, ""), AssignedToId: AssignedToId, '
              'Assignee: Coalesce(AssignedToTitle, ""), AssigneeInit: Initials(Coalesce(AssignedToTitle, "")), Priority: Priority.Value, '
              f'DueDate: DueDate, DueText: {due_text("DueDate")}, TaskStatus: TaskStatus.Value, '
              'IsOverdue: TaskStatus.Value <> "Done" && !IsBlank(DueDate) && DueDate < Today()}))')
MOCK_LOADS = ['ClearCollect(colPeople, If(MockState = "empty", Filter(MockPeople, false), MockPeople))',
              'ClearCollect(colProjects, If(MockState = "empty", Filter(MockProjects, false), MockProjects))',
              'ClearCollect(colTasks, If(MockState = "empty", Filter(MockTasks, false), MockTasks))']


def reload_block():
    """One block, repeated verbatim wherever data is (re)loaded: on entering a screen and after every write (ui-patterns section 6)."""
    loads = MOCK_LOADS if MOCK else [LOAD_PEOPLE, LOAD_PROJECTS, LOAD_TASKS]
    body = ";\n    ".join(loads)
    mock_err = 'If(MockState = "error", Set(varLoadError, "error"));\n' if MOCK else ""
    ign = "" if MOCK else " // fx-ignore FX-DELEG lists under 2,000 items by design, data row limit 2,000 (S-DELEG), baseline Q-10 agreed by Albin 2026-10-28"
    return (f"Set(varLoading, true);{ign}\nSet(varLoadError, \"\");\n"
            f"IfError(\n    {body};\n    true,\n"
            "    Set(varLoadError, If(FirstError.Kind = ErrorKind.ReadPermission, \"access\", \"error\"));\n"
            "    Set(varLoadReason, FirstError.Message));\n" + mock_err + "Set(varLoading, false)")


def ac(s, n):
    return f"AC-{s}.{n}"


# ------------------------------------------------------------------ shared pieces
def lbl(name, text, pt=9, bold=False, color="ColorText", h=18, **kw):
    n = label(name, text, size=pt, bold=bold, color=color, h=h, **kw)
    n.props["Wrap"] = "false"
    return n


def trunc(expr, n):
    """The prototype cuts a long name or description with an ellipsis (text-overflow); a label cannot, so the text is cut in the formula."""
    return f'If(Len({expr}) > {n}, Left({expr}, {n - 1}) & "…", {expr})'


def text_block(name, top, sub, top_bold=True, fp=1, top_ac=None, sub_color="ColorTextMuted"):
    """A name over a small grey line, as in .grow, td .name and td .desc."""
    return box(name, [lbl(f"{name}A", top, 9, top_bold, h=18, ac=top_ac), lbl(f"{name}B", sub, 8.5, False, sub_color, h=15)], "Vertical", 0, fp=fp)


def status_badge(name, text, fill, color, w=80):
    b = badge(name, text, fill, w=w, h=17, radius=9, size=7.5)
    b.props["Color"] = color
    # Start is the TOP of a horizontal row: centre the pill, let its height follow its text and drop the padding that made it scroll (Studio, 2026-10-28)
    b.props.update({"AlignInContainer": "AlignInContainer.Center", "AutoHeight": "true", "PaddingTop": 0, "PaddingBottom": 0, "PaddingLeft": 0, "PaddingRight": 0})
    return b


def badge_cell(name, text, fill, color, fp, w):
    """A badge in a table column: the column keeps its FillPortions (so it lines up with its header), the pill keeps its width."""
    return box(name, [status_badge(f"{name}B", text, fill, color, w=w)], "Horizontal", 0, fp=fp, align="Center")


def person_cell(name, init, who, fp):
    return box(name, [avatar(f"{name}Av", init, 20, 6.5, accessible='""'), lbl(f"{name}N", who, 9, False)], "Horizontal", 7, fp=fp, align="Center")


def progress_cell(name, pct, fp=0):
    return box(name, [svg_bar(f"{name}Bar", pct, 102, 5, "HexNeutralFill", "HexPrimary", align_in="AlignInContainer.Center"),
                      lbl(f"{name}Pct", f"={pct} & \"%\"", 9, False, w=40, ac="AC-PROJ-04.2")], "Horizontal", 8, fp=fp, w=150 if fp == 0 else None, align="Center")


def page_head(p, title, sub_expr, tools=None, ac_title=None, ac_sub=None):
    left = box(f"{p}HeadL", [label(f"{p}Title", title, size=14, bold=True, h=25, role="Heading1", ac=ac_title),
                             label(f"{p}Sub", sub_expr, size=9, color="ColorTextMuted", h=18, ac=ac_sub)], "Vertical", 2, fp=1)
    return hrow(f"{p}Head", [left] + (tools or []), 46, 8, 0, align="Center")


def card_shell(name, children, h=None, fp=None, visible=None):
    return box(name, children, "Vertical", 0, h=h, fp=fp, fill="ColorSurface", border=True, radius=CARD_R, shadow="Light", border_color="ColorDivider", visible=visible)


def th_row(name, cols, visible=None):
    kids = []
    for i, (text, fp) in enumerate(cols, 1):
        l = lbl(f"{name}H{i}", text, 8.5, False, "ColorTextMuted", h=15, fp=fp)
        kids.append(l)
    return hrow(name, kids, TH_H, 8, 0, visible, "ColorSunken", 17, "Center")


def empty_label(name, text, visible, ac_=None):
    n = label(name, text, size=9, color="ColorTextMuted", h=66, align="Center", valign="Middle", visible=visible, fp=0, ac=ac_)
    n.props["Live"] = "Live.Polite"
    return n


def state_labels(p, what, content_vis):
    """Loading, error and no-access messages (design-standards section 5); they take no space while hidden."""
    loading = label(f"{p}Loading", f'Loading {what}…', size=9, color="ColorTextMuted", h=40, visible="varLoading", fp=0)
    loading.props["Live"] = "Live.Polite"
    err = label(f"{p}LoadErr", f'=If(varLoadError = "access", "You do not have access to this data.", "The {what} could not be loaded. " & varLoadReason)',
                size=9, color="ColorError", h=40, visible='!varLoading && varLoadError <> ""', fp=0)
    err.props["Live"] = "Live.Polite"
    retry = button(f"{p}Retry", "Try again", reload_block(), "secondary", w=100, h=CTRL, visible='!varLoading && varLoadError <> ""', fp=0, size=9,
                   radius=CTRL_R, weight="FontWeight.Normal", fill="ColorSurface")
    return [loading, err, retry]


# ------------------------------------------------------------------ chrome: left navigation and top bar, placed on every screen
def top_bar(p, active_search_note=None):
    sx = f"{NAVX} + If({NARROW}, 59, {PAD})"
    sw = f"Min(357, Parent.Width - ({sx}) - 29 - {PAD} - 10 - If({NARROW}, 0, 210))"
    menu = Node(f"{p}Menu", "ModernButton@1.0.0", {"AccessibleLabel": '"Open menu"', "Height": 31, "OnSelect": "Set(varMenuOpen, !varMenuOpen) // AC-NAV-01.6",
                                                   "Text": '"☰"', "Visible": NARROW, "Width": 31, "X": 16, "Y": (TOP_H - 31) // 2})
    search = textinput(f"{p}Search", default="varSearch", hint="Search projects and tasks", h=CTRL, accessible="Search", x=f"({sx}) + 1", y=(TOP_H - CTRL) // 2,
                       w=f"({sw}) - 2", onchange=f"Set(varSearch, {p}Search.Text) // AC-NAV-02.5")
    search.props.update({"Fill": "ColorTransparent", "BorderColor": "ColorTransparent", "BorderThickness": 0, "PaddingLeft": 29, "DelayOutput": "true",
                         "FocusedBorderColor": "ColorPrimary", "FocusedBorderThickness": 2, "RadiusBottomLeft": CTRL_R, "RadiusBottomRight": CTRL_R,
                         "RadiusTopLeft": CTRL_R, "RadiusTopRight": CTRL_R})
    nodes = [label(f"{p}Top", '=""', size=9, h=TOP_H, w=f"Parent.Width - {NAVX}", x=NAVX, y=0, fill="ColorSurface"),
             rect(f"{p}TopLine", "ColorDivider", 1, w=f"Parent.Width - {NAVX}", x=NAVX, y=TOP_H - 1),
             menu,
             panel(f"{p}SearchBg", f"({sx})", (TOP_H - CTRL) // 2, sw, CTRL, fill="ColorBackground", border_color="ColorBorder", radius=CTRL_R, shadow="None"),
             svg_icon(f"{p}SearchIcon", SEARCH_ICON, "HexTextMuted", 14, x=f"({sx}) + 9", y=(TOP_H - 14) // 2, stroke=2),
             search,
             label(f"{p}Who", "=User().FullName", size=9, color="ColorText", h=18, w=200, x=f"Parent.Width - {PAD} - 29 - 10 - 200", y=(TOP_H - 18) // 2,
                   align="Right", visible=f"!({NARROW})", ac="AC-NAV-02.2"),
             avatar(f"{p}Avatar", "=Initials(User().FullName)", 29, 7.5, x=f"Parent.Width - {PAD} - 29", y=(TOP_H - 29) // 2, accessible="User().FullName")]
    nodes[-1].props["AccessibleLabel"] = "User().FullName"
    nodes[0].props["Wrap"] = "false"
    return nodes


def chrome(p, active):
    out = side_nav(p, "=AppTitle", NAV_ITEMS, active, GEO, SIDE_VISIBLE)
    out += top_bar(p)
    return out


class MtScreen(Screen):
    def __init__(self, name, prefix, active, on_visible):
        super().__init__(name, prefix, on_visible=on_visible)
        self.chrome = []
        self.active = active
        self.content = []
        self.extra_after = []

    def nodes(self):
        main = box(f"{self.p}Main", self.content, "Vertical", GAP, h=f"Parent.Height - {TOP_H}", w=f"Parent.Width - {NAVX}", y=TOP_H, fill="ColorBackground",
                   scroll=True, min0=False)
        main.props.update({"X": NAVX, "PaddingTop": PAD, "PaddingBottom": PAD, "PaddingLeft": PAD,
                           "PaddingRight": f"Max({PAD}, Parent.Width - ({NAVX}) - {PAD} - {CONTENT_MAX})"})
        return [main] + chrome(self.p, self.active) + self.extra_after


# ------------------------------------------------------------------ scrDashboard
def dashboard():
    s = MtScreen("scrDashboard", "dsh", 0, reload_block())
    p = "dsh"
    vis = '!varLoading && varLoadError = ""'
    cards = []
    specs = [("Total projects", "=CountRows(colProjects)", "DASH-01.3", False), ("Active projects", '=CountRows(Filter(colProjects, ProjectStatus = "Active"))', "DASH-01.4", False),
             ("Completed tasks", '=CountRows(Filter(colTasks, TaskStatus = "Done"))', "DASH-01.5", False), ("Overdue tasks", "=CountRows(OverdueTasks)", "DASH-01.6", True)]
    for i, (cap, expr, a, warn) in enumerate(specs, 1):
        cards.append(box(f"{p}Stat{i}", [lbl(f"{p}Stat{i}Cap", cap, 9, False, "ColorTextMuted", h=18),
                                          label(f"{p}Stat{i}Val", expr, size=18, bold=True, h=32, color="ColorError" if warn else "ColorText", ac=f"AC-{a}")],
                         "Vertical", 3, fp=1, fill="ColorSurface", pad_x=17, pad_y=15, border=True, radius=CARD_R, shadow="Light", border_color="ColorDivider"))

    def list_panel(key, head, items, empty, cells, a_rows, a_empty):
        n = f"CountRows({items})"
        head_l = label(f"{p}{key}Head", head, size=9, bold=True, h=46, valign="Middle", pad_left=17, fp=0, role="Heading2")
        head_l.props["Wrap"] = "false"
        div = rect(f"{p}{key}Div", "ColorDivider", 1)
        div.props["FillPortions"] = 0
        tbl = table(f"{p}{key}Tbl", items, cells, f"{n} * {ROW_H}", tpl=ROW_H, visible=f"{n} > 0", ac=a_rows, row_fill="ColorSurface", row_pad=17, row_gap=10)
        emp = empty_label(f"{p}{key}Empty", empty, f"{n} = 0", a_empty)
        return card_shell(f"{p}{key}", [head_l, div, tbl, emp], h=f"{HEAD_H} + If({n} = 0, 66, {n} * {ROW_H})", fp=1)

    od_cells = [text_block(f"{p}OdTxt", "=ThisItem.Title", '=ThisItem.Project & " · due " & ThisItem.DueText', top_bold=False, top_ac=None),
                status_badge(f"{p}OdBadge", "=ThisItem.Priority", PRIORITY_FILL, PRIORITY_TEXT, w=64)]
    up_cells = [text_block(f"{p}UpTxt", "=ThisItem.Title", '=ThisItem.Assignee & " · due " & ThisItem.DueText', top_bold=False),
                status_badge(f"{p}UpBadge", "=ThisItem.TaskStatus", TSTATUS_FILL, TSTATUS_TEXT, w=80)]
    od = list_panel("Od", "Overdue tasks", "OverdueTasks", "Nothing overdue. Nice work.", od_cells, "AC-DASH-02.1", "AC-DASH-02.2")
    up = list_panel("Up", "Upcoming deadlines", "UpcomingTasks", "No upcoming tasks.", up_cells, "AC-DASH-02.3", "AC-DASH-02.4")
    grid = hrow(f"{p}Grid", [od, up], f"Max({HEAD_H} + If(CountRows(OverdueTasks) = 0, 66, CountRows(OverdueTasks) * {ROW_H}), "
                f"{HEAD_H} + If(CountRows(UpcomingTasks) = 0, 66, CountRows(UpcomingTasks) * {ROW_H}))", 14, 0, align="Stretch")

    rc_cells = [text_block(f"{p}RcTxt", "=ThisItem.Title", '=ThisItem.Owner & " · due " & ThisItem.DueText', top_bold=True),
                progress_cell(f"{p}RcProg", "ThisItem.Progress"),
                status_badge(f"{p}RcBadge", "=ThisItem.ProjectStatus", PSTATUS_FILL, PSTATUS_TEXT, w=80)]
    n = "CountRows(RecentProjects)"
    rc_head = label(f"{p}RcHead", "Recent projects", size=9, bold=True, h=46, valign="Middle", pad_left=17, fp=0, role="Heading2")
    rc_head.props["Wrap"] = "false"
    rc_div = rect(f"{p}RcDiv", "ColorDivider", 1)
    rc_div.props["FillPortions"] = 0
    recent = card_shell(f"{p}Rc", [rc_head, rc_div,
                                   table(f"{p}RcTbl", "RecentProjects", rc_cells, f"{n} * {ROW_H}", tpl=ROW_H, visible=f"{n} > 0", ac="AC-DASH-03.1", row_fill="ColorSurface", row_pad=17, row_gap=10),
                                   empty_label(f"{p}RcEmpty", "No projects yet.", f"{n} = 0")],
                        h=f"{HEAD_H} + If({n} = 0, 66, {n} * {ROW_H})", fp=0)

    s.content = [page_head(p, "Dashboard", "A quick look at where your work stands.", ac_title="AC-DASH-01.1", ac_sub="AC-DASH-01.1"),
                 *state_labels(p, "dashboard", vis),
                 *cards_row(p, cards, vis), _vis(grid, vis), _vis(recent, vis)]
    return s


ROW85 = 85


def cards_row(p, cards, visible=None):
    return [hrow(f"{p}Stats", cards, ROW85, 14, 0, visible)]


def _vis(node, vis):
    node.props["Visible"] = vis
    return node


# ------------------------------------------------------------------ scrProjects
def filter_dropdown(p, items, label_text="Filter by status"):
    dd = dropdown(f"{p}Filter", items)
    dd.props.update({"AccessibleLabel": f'"{label_text}"', "Default": f"LookUp({items}, Value = varFilter)", "FillPortions": 0, "Width": 150,
                     "OnChange": f"Set(varFilter, {p}Filter.Selected.Value)", "AlignInContainer": "AlignInContainer.Center"})
    return dd


def projects():
    s = MtScreen("scrProjects", "prj", 1, reload_block())
    p = "prj"
    vis = '!varLoading && varLoadError = ""'
    new_btn = button(f"{p}New", "+ New project", 'Set(varModal, "new"); Set(varErrName, false); Set(varErrDue, false); Reset(prjName); Reset(prjDesc); Reset(prjDue); '
                     'Reset(prjOwner); SetFocus(prjName) // AC-PROJ-03.3', "primary", w=116, h=CTRL, size=9, radius=CTRL_R, fp=0, ac=None,
                     align_in="AlignInContainer.Center", weight="FontWeight.Normal")
    tools = box(f"{p}Tools", [filter_dropdown(p, "colProjectFilter"), new_btn], "Horizontal", 8, fp=0, w=274, align="Center")
    head = page_head(p, "Projects", '=CountRows(FilteredProjects) & " of " & CountRows(colProjects) & " projects"', [tools], "AC-PROJ-01.1", "AC-PROJ-01.1")
    cols = [("Project", 3), ("Owner", 2), ("Status", 1.2), ("Progress", 1.8), ("Due date", 1.2)]
    cells = [text_block(f"{p}RowTxt", "=" + trunc("ThisItem.Title", 50), "=If(IsBlank(ThisItem.Summary), \"No description\", " + trunc("ThisItem.Summary", 40) + ")", fp=3, top_ac="AC-PROJ-01.3"),
             person_cell(f"{p}RowOwn", "ThisItem.OwnerInit", "=ThisItem.Owner", 2),
             badge_cell(f"{p}RowSt", "=ThisItem.ProjectStatus", PSTATUS_FILL, PSTATUS_TEXT, 1.2, 80),
             progress_cell(f"{p}RowPr", "ThisItem.Progress", fp=1.8),
             lbl(f"{p}RowDue", "=ThisItem.DueText", 9, False, fp=1.2)]
    n = "CountRows(FilteredProjects)"
    tbl = table(f"{p}Tbl", "FilteredProjects", cells, f"{n} * {ROW_H}", tpl=ROW_H, visible=f"{n} > 0", ac="AC-PROJ-01.2", row_fill="ColorSurface", row_pad=17, row_gap=8)
    card = card_shell(f"{p}Card", [th_row(f"{p}Th", cols, f"{n} > 0"), tbl, empty_label(f"{p}Empty", "No projects match your search or filter.", f"{n} = 0", "AC-PROJ-01.7")],
                      h=f"If({n} = 0, 66, {TH_H} + {n} * {ROW_H})", fp=0, visible=vis)
    s.content = [head, *state_labels(p, "projects", vis), card]
    s.extra_after = project_dialog(p)
    return s


def project_dialog(p):
    W = 391
    shown = 'varModal = "new"'
    py = "panModal.Y"
    e1, e2 = "If(varErrName, 16, 0)", "If(varErrDue, 16, 0)"

    def y(off):
        return f"{py} + {off}"

    def x(off=20):
        return f"panModal.X + {off}"

    iw = W - 40
    half = (iw - 10) // 2
    name_in = textinput("prjName", default='""', hint="e.g. Customer portal", h=CTRL, accessible="Project name", x=x(), y=y(76), w=iw, visible=shown)
    name_in.props["BorderColor"] = "If(varErrName, ColorError, ColorBorder)"
    desc_in = textinput("prjDesc", default='""', hint="What is this project about?", h=70, multiline=True, accessible="Description", x=x(), y=y(f"144 + {e1}"), w=iw, visible=shown)
    due_in = Node("prjDue", "DatePicker@0.0.46", {"Height": CTRL, "Visible": shown, "Width": half, "X": x(20 + half + 10), "Y": y(f"248 + {e1}")})
    owner = dropdown("prjOwner", "ActivePeople")
    owner.props.update({"AccessibleLabel": '"Owner"', "Default": "First(ActivePeople)", "ItemDisplayText": "ThisItem.Name", "Visible": shown, "Width": half,
                        "X": x(), "Y": y(f"248 + {e1}")})
    for tin in (name_in, desc_in):
        tin.props.update({"FocusedBorderColor": "ColorPrimary", "FocusedBorderThickness": 2, "RadiusBottomLeft": CTRL_R, "RadiusBottomRight": CTRL_R,
                          "RadiusTopLeft": CTRL_R, "RadiusTopRight": CTRL_R, "Fill": "ColorSurface"})
    create = (
        'Set(varErrName, IsBlank(Trim(prjName.Text))); // AC-PROJ-03.5\n'
        'Set(varErrDue, IsBlank(prjDue.SelectedDate)); // AC-PROJ-03.6\n'
        'If(!varErrName && !varErrDue,\n'
        '    IfError(\n'
        + ('        Collect(colProjects, {ID: Coalesce(Max(colProjects, ID), 0) + 1, Title: Trim(prjName.Text), Summary: Trim(prjDesc.Text), OwnerId: prjOwner.Selected.ID, '
           'Owner: prjOwner.Selected.Name, OwnerInit: Initials(prjOwner.Selected.Name), ProjectStatus: "Planning", Progress: 0, DueDate: prjDue.SelectedDate, '
           f'DueText: {due_text("prjDue.SelectedDate")}}});\n' if MOCK else
           '        Patch(MT_Project, Defaults(MT_Project), {Title: Trim(prjName.Text), ProjectDescription: Trim(prjDesc.Text), OwnerId: prjOwner.Selected.ID, '
           'OwnerTitle: prjOwner.Selected.Name, ProjectStatus: {Value: "Planning"}, Progress: 0, DueDate: prjDue.SelectedDate}); // AC-PROJ-03.8\n')
        + '        Set(varModal, "");\n        Set(varFilter, "All statuses");\n        Set(varSearch, "");\n        Reset(prjSearch);\n'
        '        ' + reload_block().replace("\n", "\n        ") + ';\n'
        '        Notify("Project created", NotificationType.Success); // AC-PROJ-03.9\n'
        '        true,\n'
        '        Notify("The project was not created. " & FirstError.Message, NotificationType.Error)))')
    nodes = [
        label("prjOverlay", '=""', size=9, h="Parent.Height", w="Parent.Width", x=0, y=0, fill="ColorOverlay", visible='varModal <> ""'),
        panel("panModal", f"(Parent.Width - {W}) / 2", f"Max(12, (Parent.Height - Self.Height) / 2)", W, f"356 + {e1} + {e2}", fill="ColorSurface", border_color="ColorDivider",
              radius=CARD_R, shadow="Bold", visible=shown),
        lbl("prjModalTitle", "Create project", 11.5, True, h=20, w=iw, x=x(), y=y(20), visible=shown, role="Heading2", ac="AC-PROJ-03.1"),
        lbl("prjNameCap", "Project name", 9, False, h=18, w=iw, x=x(), y=y(54), visible=shown, ac="AC-PROJ-03.2"),
        name_in,
        label("prjNameErr", "Enter a project name.", size=7.5, color="ColorError", h=13, w=iw, x=x(), y=y(113), visible="varErrName", ac="AC-PROJ-03.5"),
        lbl("prjDescCap", "Description", 9, False, h=18, w=iw, x=x(), y=y(f"122 + {e1}"), visible=shown),
        desc_in,
        lbl("prjOwnerCap", "Owner", 9, False, h=18, w=half, x=x(), y=y(f"226 + {e1}"), visible=shown),
        lbl("prjDueCap", "Due date", 9, False, h=18, w=half, x=x(20 + half + 10), y=y(f"226 + {e1}"), visible=shown),
        owner, due_in,
        label("prjDueErr", "Choose a due date.", size=7.5, color="ColorError", h=13, w=half, x=x(20 + half + 10), y=y(f"285 + {e1}"), visible="varErrDue", ac="AC-PROJ-03.6"),
        button("prjCancel", "Cancel", 'Set(varModal, "") // AC-PROJ-03.10', "secondary", w=66, h=CTRL, x=x(W - 20 - 118 - 8 - 66), y=f"panModal.Y + panModal.Height - 54", visible=shown,
               size=9, radius=CTRL_R, weight="FontWeight.Normal", fill="ColorSurface"),
        button("prjCreate", "Create project", create, "primary", w=118, h=CTRL, x=x(W - 20 - 118), y="panModal.Y + panModal.Height - 54", visible=shown, size=9, radius=CTRL_R,
               weight="FontWeight.Normal"),
    ]
    for n_ in nodes:
        if n_.name in ("prjNameErr", "prjDueErr"):
            n_.props["Live"] = "Live.Polite"
    nodes[0].props["OnSelect"] = 'Set(varModal, "") // AC-PROJ-03.10'
    return nodes


# ------------------------------------------------------------------ scrTasks
def tasks():
    s = MtScreen("scrTasks", "tsk", 2, reload_block())
    p = "tsk"
    vis = '!varLoading && varLoadError = ""'
    tools = box(f"{p}Tools", [filter_dropdown(p, "colTaskFilter")], "Horizontal", 8, fp=0, w=158, align="Center")
    head = page_head(p, "Tasks", '=CountRows(FilteredTasks) & " of " & CountRows(colTasks) & " tasks"', [tools], "AC-TASK-01.1", "AC-TASK-01.1")
    cols = [("Task", 3), ("Assigned to", 2), ("Priority", 1), ("Due date", 1.6), ("Status", 1.8)]
    due = lbl(f"{p}RowDue", '=ThisItem.DueText & If(ThisItem.IsOverdue, " (overdue)", "")', 9, False, fp=1.6, ac="AC-TASK-01.5")
    due.props["Color"] = "If(ThisItem.IsOverdue, ColorError, ColorText)"
    prio = badge_cell(f"{p}RowPr", "=ThisItem.Priority", PRIORITY_FILL, PRIORITY_TEXT, 1, 64)
    status = dropdown(f"{p}RowSt", "colTaskStatus")
    patch = (('Patch(colTasks, LookUp(colTasks, ID = ThisItem.ID), {TaskStatus: Self.Selected.Value}); ' if MOCK else
              'Patch(MT_Task, LookUp(MT_Task, ID = ThisItem.ID), {TaskStatus: {Value: Self.Selected.Value}}); // AC-TASK-03.2\n    ') +
             reload_block().replace("\n", "\n    ") + ';\n    Notify("Task status updated", NotificationType.Success); // AC-TASK-03.2\n    true')
    onchange = ('If(Self.Selected.Value <> ThisItem.TaskStatus,\n  IfError(\n    ' + patch + ',\n'
                '    Notify(If(FirstError.Kind = ErrorKind.EditPermissions, "You don\'t have access to change this task.", "The status was not changed. " & FirstError.Message), '
                'NotificationType.Error)))')
    status.props.update({"AccessibleLabel": '="Status for " & ThisItem.Title', "Default": "LookUp(colTaskStatus, Value = ThisItem.TaskStatus)", "FillPortions": 1.8,
                         "OnChange": onchange, "AlignInContainer": "AlignInContainer.Center"})
    cells = [text_block(f"{p}RowTxt", "=" + trunc("ThisItem.Title", 50), "=" + trunc("ThisItem.Project", 40), fp=3, top_ac="AC-TASK-01.3"),
             person_cell(f"{p}RowAs", "ThisItem.AssigneeInit", "=ThisItem.Assignee", 2), prio, due, status]
    n = "CountRows(FilteredTasks)"
    tbl = table(f"{p}Tbl", "FilteredTasks", cells, f"{n} * {ROW_H}", tpl=ROW_H, visible=f"{n} > 0", ac="AC-TASK-01.2", row_fill="ColorSurface", row_pad=17, row_gap=8)
    card = card_shell(f"{p}Card", [th_row(f"{p}Th", cols, f"{n} > 0"), tbl, empty_label(f"{p}Empty", "No tasks match your search or filter.", f"{n} = 0", "AC-TASK-01.7")],
                      h=f"If({n} = 0, 66, {TH_H} + {n} * {ROW_H})", fp=0, visible=vis)
    s.content = [head, *state_labels(p, "tasks", vis), card]
    return s


# ------------------------------------------------------------------ App.pa.yaml
def mock_data():
    people = [(1, "Priya Nair"), (2, "Daniel Kim"), (3, "Sofia Rossi"), (4, "Marcus Lee"), (5, "Aisha Khan")]
    mail = lambda n: n.lower().replace(" ", ".") + "@example.com"
    mp = "Table(" + ", ".join(f'{{ID: {i}, Name: "{n}", Email: "{mail(n)}", Active: true}}' for i, n in people) + ", {ID: 6, Name: \"Former Member\", Email: \"former.member@example.com\", Active: false})"
    projects = [(1, "Website redesign", "Refresh the marketing site with a new design system.", 1, "Active", 65, 21), (2, "Mobile app v2", "Rebuild onboarding and add offline mode.", 2, "Active", 40, 45),
                (3, "Customer portal", "Self-service portal for invoices and support.", 3, "Planning", 10, 90), (4, "Data warehouse", "Consolidate reporting data into one warehouse.", 4, "On hold", 30, 60),
                (5, "Brand guidelines", "Document logo, colour and tone of voice.", 5, "Completed", 100, -12), (6, "Security audit", "Annual access review and policy updates.", 2, "Active", 80, 7),
                (7, "Vendor onboarding programme for the regional finance and procurement teams", "", 4, "Planning", 0, 120)]
    name = dict(people)
    pr = "Table(" + ", ".join(
        f'{{ID: {i}, Title: "{t}", Summary: "{sm}", OwnerId: {o}, Owner: "{name[o]}", OwnerInit: Initials("{name[o]}"), ProjectStatus: "{st}", Progress: {pg}, '
        f'DueDate: DateAdd(Today(), {dd}, TimeUnit.Days), DueText: {due_text(f"DateAdd(Today(), {dd}, TimeUnit.Days)")}}}' for i, t, sm, o, st, pg, dd in projects) + ")"
    tasks_ = [(1, "Finalize homepage wireframes", "Website redesign", 1, "High", -3, "In progress"), (2, "Write launch copy", "Website redesign", 5, "Medium", 5, "To do"),
              (3, "Set up push notifications", "Mobile app v2", 2, "High", 9, "In progress"), (4, "Design offline sync states", "Mobile app v2", 3, "Medium", -1, "To do"),
              (5, "Interview five customers", "Customer portal", 3, "Low", 14, "To do"), (6, "Define warehouse schema", "Data warehouse", 4, "High", -6, "To do"),
              (7, "Export final logo pack", "Brand guidelines", 5, "Low", -14, "Done"), (8, "Review admin permissions", "Security audit", 2, "High", 3, "In progress"),
              (9, "Update password policy", "Security audit", 4, "Medium", -20, "Done"), (10, "QA the checkout flow", "Website redesign", 1, "Medium", 12, "Done")]
    pid = {t: i for i, t, *_ in projects}
    ts = "Table(" + ", ".join(
        f'{{ID: {i}, Title: "{t}", ProjectId: {pid[pj]}, Project: "{pj}", AssignedToId: {a}, Assignee: "{name[a]}", AssigneeInit: Initials("{name[a]}"), Priority: "{pri}", '
        f'DueDate: DateAdd(Today(), {dd}, TimeUnit.Days), DueText: {due_text(f"DateAdd(Today(), {dd}, TimeUnit.Days)")}, TaskStatus: "{st}", IsOverdue: {"true" if st != "Done" and dd < 0 else "false"}}}'
        for i, t, pj, a, pri, dd, st in tasks_) + ")"
    return mp, pr, ts


def app_yaml():
    named = [
        '// Rules used on more than one screen are defined once here (D5). Collections are loaded by each screen (ui-patterns section 6).',
        'AppTitle = "Taskboard";',
        'BreakpointNarrow = 646;  // 760 px at the prototype scale 0.85 (AC-NAV-01.6)',
        '// The first letters of the first two words of a name, as the prototype\'s initials() does (AC-NAV-02.2)',
        'Initials(n: Text): Text = Upper(Left(n, 1) & If(IsBlank(Find(" ", n)), "", Mid(n, Find(" ", n) + 1, 1)));',
        'OverdueTasks = Filter(colTasks, IsOverdue);  // not Done and due before today, defined once (AC-DASH-01.6)',
        'UpcomingTasks = FirstN(SortByColumns(Filter(colTasks, TaskStatus <> "Done" && DueDate >= Today()), "DueDate", SortOrder.Ascending), 5);  // AC-DASH-02.3',
        'RecentProjects = FirstN(SortByColumns(colProjects, "ID", SortOrder.Descending), 5);  // AC-DASH-03.1',
        'ActivePeople = Filter(colPeople, Active);  // AC-TEAM-01.1',
        'FilteredProjects = Filter(colProjects, (varFilter = "All statuses" || ProjectStatus = varFilter) && (IsBlank(Trim(varSearch)) || Lower(Trim(varSearch)) in Lower(Title & " " & Owner & " " & Summary)));  // AC-PROJ-02.4',
        'FilteredTasks = Filter(colTasks, (varFilter = "All statuses" || TaskStatus = varFilter) && (IsBlank(Trim(varSearch)) || Lower(Trim(varSearch)) in Lower(Title & " " & Assignee & " " & Project)));  // AC-TASK-02.4',
    ]
    if MOCK:
        mp, pr, ts = mock_data()
        named += ['MockState = "ready";  // ready, empty or error - lets a reviewer see each state until G8', f"MockPeople = {mp};", f"MockProjects = {pr};", f"MockTasks = {ts};"]
    tok = mt_app.tokens_text()
    on_start = ('Set(varFilter, "All statuses");\nSet(varSearch, "");\nSet(varMenuOpen, false);\nSet(varModal, "");\nSet(varErrName, false);\nSet(varErrDue, false);\n'
                'Set(varLoading, false);\nSet(varLoadError, "");\nSet(varLoadReason, "");\n'
                + ('ClearCollect(colProjectFilter, {Value: "All statuses"}, {Value: "Planning"}, {Value: "Active"}, {Value: "On hold"}, {Value: "Completed"});\n'
                   'ClearCollect(colTaskFilter, {Value: "All statuses"}, {Value: "To do"}, {Value: "In progress"}, {Value: "Done"});\n'
                   'ClearCollect(colTaskStatus, {Value: "To do"}, {Value: "In progress"}, {Value: "Done"})' if MOCK else
                   'ClearCollect(colProjectFilter, {Value: "All statuses"});\nCollect(colProjectFilter, Choices(MT_Project.ProjectStatus));\n'
                   'ClearCollect(colTaskFilter, {Value: "All statuses"});\nCollect(colTaskFilter, Choices(MT_Task.TaskStatus));\n'
                   'ClearCollect(colTaskStatus, Choices(MT_Task.TaskStatus))'))
    text = ["App:", "  Properties:", "    Formulas: |-"]
    text += [l for l in tok.rstrip("\n").split("\n")]
    text[3] = text[3]  # first line starts with =
    text += ["      " + l for l in ("\n".join(named)).split("\n")]
    text += ["    OnStart: |-"] + ["      " + ("=" + l if i == 0 else l) for i, l in enumerate(on_start.split("\n"))]
    text += ["    StartScreen: =scrDashboard", "    Theme: =PowerAppsTheme"]
    return "\n".join(text) + "\n"


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    (SRC / "App.pa.yaml").write_text(app_yaml(), encoding="utf-8")
    for fn in (dashboard, projects, tasks):
        sc = fn()
        sc.write(SRC)
        print("wrote", sc.name)
    old = SRC / "scrHome.pa.yaml"
    if old.exists():
        old.unlink()
        print("removed scrHome")
    (SRC / "_EditorState.pa.yaml").write_text("EditorState:\n  ScreensOrder:\n    - scrDashboard\n    - scrProjects\n    - scrTasks\n", encoding="utf-8")


if __name__ == "__main__":
    main()
