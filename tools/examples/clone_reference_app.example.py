"""WORKED EXAMPLE (not run by default): how a project cloned its Studio-built reference app. Copy this file, change the mapping to your lists, columns and flows, and run it.
It was written for a COI request app; the list prefix here is PRJ_ and the flows are named 'Request - ...'.

Clones the hand-built reference app (samples/powerapp/Src, unpacked with `pac canvas unpack --layout SourceCode`) into canvas/COI/Src.

Run: uv run tools/examples/clone_reference_app.example.py   (then uv run tools/pp.py build)

Layout, names, sizes and positions are kept exactly. What changes:
  * RGBA literals become the design tokens that hold the same values (D11);
  * list names become the PRJ_ lists, and the collections are loaded in the SAME SHAPE as the hand-built app's
    (so its formulas keep working), by ForAll over our lists;
  * the buttons that only simulated an action now call our flows, write the Activity list and reload;
  * small additions: loading / error / empty messages, AC IDs in comments, and a few fixes noted inline."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE = ROOT / "samples" / "powerapp" / "Src"
SRC = ROOT / "canvas" / "StarterApp" / "Src"  # your app's source folder
NL = chr(10)

# ---------------------------------------------------------------- colours -> tokens
TOKENS = {
    "255, 255, 255, 1": "ColorBackground", "32, 31, 30, 1": "ColorText", "243, 242, 241, 1": "ColorSurface", "15, 108, 189, 1": "ColorPrimary",
    "161, 159, 157, 1": "ColorDisabled", "0, 0, 0, 0": "ColorTransparent", "16, 94, 165, 1": "ColorPrimaryHover", "12, 76, 134, 1": "ColorPrimaryPressed",
    "96, 94, 92, 1": "ColorTextMuted", "0, 0, 0, 0.12": "ColorPressedOverlay", "0, 0, 0, 0.06": "ColorHoverOverlay", "254, 217, 168, 1": "ColorWarningFill",
    "188, 215, 242, 1": "ColorInfoFill", "255, 255, 255, 0.8": "ColorOnSecondaryMuted", "196, 49, 75, 1": "ColorError", "15, 42, 74, 1": "ColorSecondary",
    "244, 182, 182, 1": "ColorErrorFill", "221, 221, 221, 1": "ColorNeutralFill", "199, 233, 192, 1": "ColorSuccessFill", "255, 244, 206, 1": "ColorNoteFill",
    "232, 201, 90, 1": "ColorNoteBorder", "170, 40, 62, 1": "ColorErrorHover", "140, 30, 50, 1": "ColorErrorPressed", "0, 0, 0, 0.45": "ColorOverlay",
}
NEW_TOKENS = """      // Colours of the hand-built reference app (samples/powerapp), kept so the screens look the same
      ColorDisabled = RGBA(161, 159, 157, 1);
      ColorHoverOverlay = RGBA(0, 0, 0, 0.06);
      ColorPressedOverlay = RGBA(0, 0, 0, 0.12);
      ColorOnSecondaryMuted = RGBA(255, 255, 255, 0.8);
      ColorNoteBorder = RGBA(232, 201, 90, 1);
      ColorErrorHover = RGBA(170, 40, 62, 1);
      ColorErrorPressed = RGBA(140, 30, 50, 1);
"""
LIGHT_ON_DARK = {"Color", "HoverColor", "PressedColor"}


def recolour(text):
    out, ctrl = [], ""
    for line in text.split(NL):
        m = re.match(r"^\s*Control:\s*(\S+)", line)
        if m:
            ctrl = m.group(1)

        def sub(mm):
            raw = mm.group(1)
            key = re.sub(r"\s+", " ", raw.strip())
            if key == "210, 208, 206, 1":
                p = re.match(r"^\s*(\w+):", line)
                prop = p.group(1) if p else ""
                # outlines of inputs and buttons use the darker, accessible border (design-spec section 8)
                return "ColorBorder" if (ctrl in ("Classic/Button@2.2.0", "Classic/TextInput@2.3.2") and "Border" in prop) else "ColorDivider"
            if key == "255, 255, 255, 1":
                p = re.match(r"^\s*(\w+):", line)
                return "ColorOnPrimary" if (p and p.group(1) in LIGHT_ON_DARK) else "ColorBackground"
            assert key in TOKENS, f"unmapped colour {key}: {line.strip()[:80]}"
            return TOKENS[key]
        out.append(re.sub(r"RGBA\(([^)]*)\)", sub, line))
    return NL.join(out)


# ---------------------------------------------------------------- data blocks (collections in the hand-built app's shape)
RELOAD = ('ClearCollect(colReqs, ForAll(If(varIsTreasury, Filter(PRJ_CoiRequest, RequestStatus.Value <> "Draft"), Filter(PRJ_CoiRequest, RequestorEmail = User().Email)), '
          '{ID: ID, Title: Title, ProjectName: ProjectName, BloomPOC: PocEmail, CustomerName: CustomerName, CertificateHolder: CertificateHolderName, '
          'HolderAddress: CertificateHolderAddress, Language: Language.Value, AdditionalInsured: AdditionalInsured, '
          'WaiverOfSubrogation: If(WaiverOfSubrogation, "Yes", "No"), Status: RequestStatus.Value, Reviewed: Reviewed, SubmittedDate: SubmittedOn, '
          'RequestorName: RequestorName, RequestorEmail: RequestorEmail, TreasuryNotes: TreasuryNotes, RectificationNotes: RectificationNotes, '
          'FinalCOIFile: SentDocumentName})); ClearCollect(colHolders, {Value: "All"}); Collect(colHolders, Distinct(colReqs, CertificateHolder)); Clear(colDocs); '
          'If(varIsTreasury, Collect(colDocs, ForAll(PRJ_COIDocuments, {ID: ID, Title: \'{FilenameWithExtension}\', CertificateHolder: CertificateHolderName, '
          'RequestID: CoiRequestTitle, DocumentType: DocumentType.Value, Version: DocumentVersion, DocStatus: DocumentStatus.Value, Link: \'{Link}\'})))')
DETAIL = ('Set(varReq, LookUp(colReqs, ID = varReq.ID)); '
          'ClearCollect(colCovDetail, ForAll(Filter(PRJ_CoiCoverage, CoiRequestId = varReq.ID), {Title: CoiRequestTitle, CoverageName: Title, '
          'OccurrenceLimit: OccurrenceLimit, AggregateLimit: AggregateLimit})); '
          'ClearCollect(colActivity, ForAll(Filter(PRJ_CoiActivity, CoiRequestId = varReq.ID), {Title: CoiRequestTitle, Activity: Title, ActivityDate: ActivityOn, ActionBy: ActionBy}))')
FAIL = 'If(FirstError.Kind = ErrorKind.ReadPermission, "You do not have access to this data.", "We could not load the data. Select Dashboard to try again.")'
LATEST = 'First(Sort(Filter(colDocs, RequestID = varReq.Title && DocumentType = "AON COI" && DocStatus = "Active"), Version, SortOrder.Descending))'


def loaded(body):
    """A guarded load: a loading flag, and the reason when it fails (STD-STATES)."""
    return f'Set(varLoading, true); Set(varLoadError, ""); IfError({body}, Set(varLoadError, {FAIL})); Set(varLoading, false)'


def act(text):
    return (f'Patch(PRJ_CoiActivity, Defaults(PRJ_CoiActivity), {{Title: "{text}", CoiRequestId: varReq.ID, CoiRequestTitle: varReq.Title, '
            f'ActivityOn: Now(), ActionBy: User().FullName}})')


def flow(run, acts, ok, fail, extra=""):
    steps = [run] + [act(a) for a in acts] + ["Refresh(PRJ_CoiRequest)", "Refresh(PRJ_COIDocuments)", RELOAD, DETAIL]
    if extra:
        steps.append(extra)
    steps.append(f'Notify("{ok}", NotificationType.Success)')
    return "IfError(" + NL + (";" + NL).join("    " + s for s in steps) + "," + NL + f'    Notify("{fail}", NotificationType.Error))'


# ---------------------------------------------------------------- YAML text helpers
def indent_of(line):
    return len(line) - len(line.lstrip())


def block_range(lines, ctrl):
    for i, l in enumerate(lines):
        if re.match(rf"^\s*- {re.escape(ctrl)}:\s*$", l):
            d = indent_of(l)
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or indent_of(lines[j]) > d):
                j += 1
            return i, j, d
    raise KeyError(ctrl)


def fmt_prop(prop, value, pad):
    value = value if value.startswith("=") else "=" + value
    if NL in value:
        return [f"{' ' * pad}{prop}: |-"] + [f"{' ' * (pad + 2)}{ln}" for ln in value.split(NL)]
    if ": " in value or value.endswith(":"):
        return [f"{' ' * pad}{prop}: '" + value.replace("'", "''") + "'"]
    return [f"{' ' * pad}{prop}: {value}"]


def set_prop(lines, ctrl, prop, value):
    i, j, d = block_range(lines, ctrl)
    pad = d + 6
    k = None
    for x in range(i + 1, j):
        if lines[x].strip().startswith("Children:") and indent_of(lines[x]) == d + 4:
            j = x
            break
    for x in range(i + 1, j):
        if indent_of(lines[x]) == pad and re.match(rf"\s*{prop}:", lines[x]):
            k = x
            break
    new = fmt_prop(prop, value, pad)
    if k is None:
        p = next(x for x in range(i + 1, j) if lines[x].strip() == "Properties:")
        lines[p + 1:p + 1] = new
        return
    e = k + 1
    while e < j and (not lines[e].strip() or indent_of(lines[e]) > pad):
        e += 1
    lines[k:e] = new


def comment(lines, ctrl, prop, ids):
    """Append the AC IDs to a property as a comment (dev-standards section 9)."""
    i, j, d = block_range(lines, ctrl)
    pad = d + 6
    for x in range(i + 1, j):
        if indent_of(lines[x]) == pad and re.match(rf"\s*{prop}:", lines[x]):
            e = x + 1
            while e < j and (not lines[e].strip() or indent_of(lines[e]) > pad):
                e += 1
            if "//" not in lines[e - 1]:
                last = lines[e - 1].rstrip()
                if last.endswith("'") and re.match(r"^\s*\w+: '", last) and e - 1 == x:
                    # a single-quoted value: the comment goes inside the quotes, or the YAML breaks (PA1001)
                    lines[e - 1] = last[:-1] + f" // {ids}'"
                else:
                    lines[e - 1] = last + f" // {ids}"
            return
    raise KeyError((ctrl, prop))


def remove_ctrl(lines, ctrl):
    i, j, d = block_range(lines, ctrl)
    del lines[i:j]


def insert_after(lines, ctrl, block):
    i, j, d = block_range(lines, ctrl)
    lines[j:j] = block


def msg_label(name, text, visible, d, height=28, color="ColorTextMuted", bold=False):
    pad = d + 6
    ls = [f"{' ' * d}- {name}:", f"{' ' * (d + 4)}Control: Label@2.5.1", f"{' ' * (d + 4)}Properties:",
          f"{' ' * pad}Color: ={color}", f"{' ' * pad}Font: =FontBody"]
    if bold:
        ls.append(f"{' ' * pad}FontWeight: =FontWeight.Semibold")
    ls += [f"{' ' * pad}Height: ={height}", f"{' ' * pad}Size: =12"]
    ls += fmt_prop("Text", text, pad)
    ls += fmt_prop("Visible", visible, pad)
    return ls


def set_screen_prop(lines, prop, value):
    # screen properties sit at indent 6 under `Properties:` at indent 4
    for x, l in enumerate(lines):
        if indent_of(l) == 6 and re.match(rf"\s*{prop}:", l):
            e = x + 1
            while e < len(lines) and (not lines[e].strip() or indent_of(lines[e]) > 6):
                e += 1
            lines[x:e] = fmt_prop(prop, value, 6)
            return
    p = next(x for x, l in enumerate(lines) if l.strip() == "Properties:" and indent_of(l) == 4)
    lines[p + 1:p + 1] = fmt_prop(prop, value, 6)


# ---------------------------------------------------------------- the transformation
def convert(name):
    text = (SAMPLE / f"{name}.pa.yaml").read_text(encoding="utf-8")
    text = NL.join(l for l in text.split(NL) if not l.startswith("#"))
    # the hand-built app's reload blocks, in any layout of whitespace, become ours
    pat_reload = (r'ClearCollect\(colReqs, If\(varIsTreasury, Filter\(COI_Requests, Status <> "Draft"\), Filter\(COI_Requests, RequestorEmail = User\(\)\.Email\)\)\);\s*'
                  r'ClearCollect\(colHolders, \{Value: "All"\}\);\s*Collect\(colHolders, Distinct\(colReqs, CertificateHolder\)\);\s*'
                  r'ClearCollect\(colDocs, If\(varIsTreasury, COI_Documents, FirstN\(COI_Documents, 0\)\)\)')
    pat_detail = (r'Set\(varReq, LookUp\(colReqs, ID = varReq\.ID\)\);\s*ClearCollect\(colCovDetail, Filter\(COI_Coverages, Title = varReq\.Title\)\);\s*'
                  r'ClearCollect\(colActivity, Filter\(COI_Activity, Title = varReq\.Title\)\)')
    text = re.sub(pat_reload, lambda m: RELOAD, text)
    text = re.sub(pat_detail, lambda m: DETAIL, text)
    text = text.replace("COI_TreasuryMembers", "PRJ_TreasuryContact").replace("COI_Requests", "PRJ_CoiRequest").replace("COI_Coverages", "PRJ_CoiCoverage")
    text = text.replace("COI_Activity", "PRJ_CoiActivity").replace("COI_Documents", "PRJ_COIDocuments")
    text = text.replace("Font.'Segoe UI'", "FontBody")
    text = text.replace('DocumentType = "Existing COI" && CertificateHolder = varReq.CertificateHolder', 'DocumentType = "Existing COI" && DocStatus = "Active" && CertificateHolder = varReq.CertificateHolder')
    return recolour(text)


def to_lines(t):
    return t.split(NL)


# ---- scrDashboard
d = to_lines(convert("scrDashboard"))
set_screen_prop(d, "OnVisible", loaded(RELOAD))
insert_after(d, "dshQHead", msg_label("dshMsg", '=If(varLoading, "Loading...", varLoadError)', "varLoading || !IsBlank(varLoadError)", 12, color="ColorError", bold=True) +
             msg_label("dshEmpty", '=If(varIsTreasury, "No requests found.", "You have no COI requests yet. Select + New COI Request to start one.")',
                       "!varLoading && IsBlank(varLoadError) && CountRows(colReqs) = 0", 12))
for c, p, ids in [("dshHdrTitle", "Text", "AC-HDR-01.1"), ("dshHdrUser", "Text", "AC-HDR-01.2"), ("dshTabDash", "OnSelect", "AC-HDR-01.3"),
                  ("dshNew", "OnSelect", "AC-MYREQ-01.4"), ("dshT1Num", "Text", "AC-DASH-01.1 AC-DASH-01.2"), ("dshR1Num", "Text", "AC-DASH-01.1 AC-DASH-01.2"),
                  ("txtQSearch", "HintText", "AC-QUE-01.3"), ("drpQStatus", "Items", "AC-QUE-01.4"), ("galQueue", "Items", "AC-QUE-01.1 AC-QUE-01.2 AC-QUE-01.5"),
                  ("dshTCView", "OnSelect", "AC-QUE-01.6"), ("galMine", "Items", "AC-MYREQ-01.1 AC-MYREQ-01.2"), ("dshRCView", "OnSelect", "AC-MYREQ-01.3")]:
    comment(d, c, p, ids)
dash = NL.join(d)

# ---- scrForm
COV_NAMES = "colCov"
FIELDS = ("{ProjectName: Trim(txtPN.Text), PocEmail: txtPOC.Text, CustomerName: txtCU.Text, CertificateHolderName: Trim(txtCH.Text), "
          "CertificateHolderAddress: txtAD.Text, Language: {Value: varLang}, AdditionalInsured: txtAI.Text, WaiverOfSubrogation: varWos = \"Yes\", "
          "RequestStatus: {Value: STATUS}, Reviewed: false, SubmittedOn: SUBMITTED, RequestorName: If(varForm.ID = 0, User().FullName, varForm.RequestorName), "
          "RequestorEmail: If(varForm.ID = 0, User().Email, varForm.RequestorEmail)}")
CORE = ("IfError(" + NL +
        "    Set(varSaved, Patch(PRJ_CoiRequest, If(varForm.ID = 0, Defaults(PRJ_CoiRequest), LookUp(PRJ_CoiRequest, ID = varForm.ID)), FIELDS));" + NL +
        "    If(varForm.ID = 0, Set(varSaved, Patch(PRJ_CoiRequest, varSaved, {Title: \"COI-\" & (1000 + varSaved.ID)}))); // AC-REQ-01.4 request ID from the item ID" + NL +
        "    ClearCollect(colOldCov, Filter(PRJ_CoiCoverage, CoiRequestId = varSaved.ID));" + NL +
        "    ForAll(Filter(colCov, Sel) As c, Patch(PRJ_CoiCoverage, Defaults(PRJ_CoiCoverage), {Title: c.CovName, CoiRequestId: varSaved.ID, CoiRequestTitle: varSaved.Title, "
        "OccurrenceLimit: Value(c.Occ), AggregateLimit: Value(c.Agg), LimitCurrencyCode: \"USD\"})); // AC-REQ-02.5" + NL +
        "    ForAll(colOldCov As o, Remove(PRJ_CoiCoverage, o))," + NL +
        "    Notify(\"We could not save the request. Your entries are kept.\", NotificationType.Error); Set(varSaved, Blank()))")
BAD_LIMITS = "Filter(colCov, Sel && (IsBlank(Occ) || IsBlank(Agg) || IsError(Value(Occ)) || IsError(Value(Agg))))"


def indent(s, n):
    return NL.join(" " * n + ln for ln in s.split(NL))


def save_formula(draft):
    status, submitted = ('"Draft"', "If(varForm.ID = 0, Blank(), varForm.SubmittedDate)") if draft else ('"Treasury Review"', "If(IsBlank(varForm.SubmittedDate), Now(), varForm.SubmittedDate)")
    core = CORE.replace("FIELDS", FIELDS.replace("STATUS", status).replace("SUBMITTED", submitted))
    resub = 'varEditing && varForm.Status = "Information Required"'
    if draft:
        tail = RELOAD + ";" + NL + 'Notify(varSaved.Title & " saved as draft.", NotificationType.Success);' + NL + "Navigate(scrDashboard, ScreenTransition.None)"
        return ("Set(varSaving, true);" + NL + core + ";" + NL + "If(!IsBlank(varSaved)," + NL + indent(tail, 4) + ");" + NL + "Set(varSaving, false) // AC-REQ-03.1 AC-REQ-03.2")
    run = (f"IfError('Request - Notify Treasury of submission'.Run(varSaved.ID, {resub}), "
           "Notify(\"Saved, but Treasury could not be notified. Ask Treasury to check the queue.\", NotificationType.Warning))")
    tail = (f"{run}; // AC-NOTIFY-01.1" + NL +
            f'Patch(PRJ_CoiActivity, Defaults(PRJ_CoiActivity), {{Title: If({resub}, "Requestor resubmitted", "Request submitted"), CoiRequestId: varSaved.ID, CoiRequestTitle: varSaved.Title, ActivityOn: Now(), ActionBy: User().FullName}});' + NL +
            f'Patch(PRJ_CoiActivity, Defaults(PRJ_CoiActivity), {{Title: "Treasury notified", CoiRequestId: varSaved.ID, CoiRequestTitle: varSaved.Title, ActivityOn: Now(), ActionBy: User().FullName}});' + NL +
            "Refresh(PRJ_CoiRequest);" + NL + RELOAD + ";" + NL + "Set(varReq, LookUp(colReqs, ID = varSaved.ID));" + NL + DETAIL.replace("Set(varReq, LookUp(colReqs, ID = varReq.ID)); ", "") + ";" + NL +
            f'Notify(varSaved.Title & If({resub}, " resubmitted", " submitted") & " successfully.", NotificationType.Success);' + NL + "Navigate(scrDetail, ScreenTransition.None)")
    return ("If(IsBlank(Trim(txtPN.Text)) || IsBlank(Trim(txtCH.Text))," + NL +
            '    Notify("Project Name and Certificate Holder Name are required.", NotificationType.Error), // AC-REQ-01.3' + NL +
            "    CountRows(Filter(colCov, Sel)) = 0," + NL + '    Notify("Tick at least one coverage.", NotificationType.Error), // AC-REQ-02.4' + NL +
            f"    CountRows({BAD_LIMITS}) > 0," + NL +
            f'    Notify("Give both limits, as numbers, for " & Concat({BAD_LIMITS}, CovName, "; ") & ".", NotificationType.Error), // AC-REQ-02.3' + NL +
            "    Set(varSaving, true);" + NL + indent(core, 4) + ";" + NL + "    If(!IsBlank(varSaved)," + NL + indent(tail, 8) + ");" + NL +
            "    Set(varSaving, false)) // AC-RESUB-01.4")


f = to_lines(convert("scrForm"))
set_prop(f, "frmSave", "OnSelect", save_formula(True))
set_prop(f, "frmSubmit", "OnSelect", save_formula(False))
# The coverage section was sized for 13 rows (610 / 520 high) and left a big empty block with fewer; and its 44-wide "Select" header wrapped to "Sele/ct".
set_prop(f, "galCovWrap", "Height", "CountRows(colCov) * 40")
set_prop(f, "frmSecC", "Height", "94 + CountRows(colCov) * 40")
set_prop(f, "frmCovH1", "Width", "56")
set_prop(f, "frmCovSel", "Width", "56")
set_prop(f, "frmSave", "DisplayMode", "If(varSaving, DisplayMode.Disabled, DisplayMode.Edit)")
set_prop(f, "frmSubmit", "DisplayMode", "If(varSaving, DisplayMode.Disabled, DisplayMode.Edit)")
for c, p, ids in [("frmTitle", "Text", "AC-REQ-01.1"), ("frmNote", "Text", "AC-RESUB-01.2"), ("segLang1", "OnSelect", "AC-REQ-01.1"), ("segWos1", "OnSelect", "AC-REQ-01.2"),
                  ("galCov", "Items", "AC-REQ-02.1"), ("frmCovSel", "OnSelect", "AC-REQ-02.2")]:
    comment(f, c, p, ids)
form = NL.join(f)

# ---- scrDetail
def doc_id(): return LATEST + ".ID"
def doc_link(): return LATEST + ".Link"


MORE = ("If(IsBlank(Trim(txtTN.Text))," + NL + '    Notify("Enter Treasury Notes first.", NotificationType.Error), // AC-RESUB-01.1' + NL + "    " +
        indent(flow("'Request - Return for information'.Run(varReq.ID, Trim(txtTN.Text))", ["Treasury requested additional information"],
                    "Sent to requestor. Status: Information Required.", "We could not return the request. It was not changed.", extra="Reset(txtTN)"), 4).lstrip() + ") // AC-RESUB-01.2 AC-RESUB-01.3")
SEND = flow(f"'Request - Send COI to requestor'.Run(varReq.ID, {doc_id()})", ["COI sent to requestor", "Request completed"], "COI sent to the requestor.",
            "We could not send the COI. The request was not changed.") + " // AC-SEND-01.1 AC-SEND-01.2 AC-SEND-01.3"
LIBSEND = flow("'Request - Send COI to requestor'.Run(varReq.ID, ThisItem.ID)", ["COI sent to requestor", "Request completed"], "COI sent to the requestor.",
               "We could not send the COI. The request was not changed.", extra="Set(varShowLib, false)") + " // AC-LIB-01.4 AC-SEND-01.1"
AON = flow("'Request - Send to AON'.Run(varReq.ID, \"New\", \"\", 0)", ["Treasury reviewed request", "New COI requested from AON"],
           "Request sent to AON. Status: Awaiting AON.", "We could not send the request to AON. It was not changed.", extra='Set(varModal, ""); Set(varShowLib, false)') + " // AC-AON-01.2 AC-AON-01.3 AC-AON-01.4"
CHG = ("If(IsBlank(Trim(txtAonChg.Text))," + NL + '    Notify("Enter notes describing the changes required.", NotificationType.Error), // AC-LIB-01.5' + NL + "    " +
       indent(flow("'Request - Send to AON'.Run(varReq.ID, \"Changes\", Trim(txtAonChg.Text), varModalDocId)", ["Treasury reviewed request", "Existing COI sent to AON for changes"],
                   "Existing COI sent to AON. Status: Awaiting AON.", "We could not send the COI to AON. It was not changed.",
                   extra='Reset(txtAonChg); Set(varModal, ""); Set(varShowLib, false)'), 4).lstrip() + ")")
UPL = flow("'Request - File uploaded COI'.Run(varReq.ID)", ["COI received from AON"], "COI filed. Status: COI Received.",
           "We could not file the upload. Check that a PDF is attached to the request.", extra='Set(varModal, "")') + " // AC-RCV-02.1"
RECT = ("If(IsBlank(Trim(txtRect.Text))," + NL + '    Notify("Enter the rectification notes.", NotificationType.Error), // AC-RECT-01.2' + NL + "    " +
        indent(flow("'Request - Send to AON'.Run(varReq.ID, \"Rectification\", Trim(txtRect.Text), 0)", ["Rectification requested"], "Rectification sent to AON.",
                    "We could not send the rectification. It was not changed.", extra='Set(varModal, "")'), 4).lstrip() + ") // AC-RECT-01.3")
EDIT = ('Set(varForm, varReq); Set(varEditing, true); Set(varLang, varReq.Language); Set(varWos, varReq.WaiverOfSubrogation); '
        'ClearCollect(colCov, ForAll(colCoverageNames As c, {CovName: c.N, Sel: !IsBlank(LookUp(colCovDetail, CoverageName = c.N)), '
        'Occ: Text(LookUp(colCovDetail, CoverageName = c.N).OccurrenceLimit), Agg: Text(LookUp(colCovDetail, CoverageName = c.N).AggregateLimit)})); '
        'Navigate(scrForm, ScreenTransition.None)')

t = to_lines(convert("scrDetail"))
set_screen_prop(t, "OnVisible", 'Set(varModal, ""); Set(varShowLib, false);' + NL + loaded(RELOAD + "; " + DETAIL))
remove_ctrl(t, "dtlBSim")
set_prop(t, "dtlEdit", "OnSelect", EDIT)
set_prop(t, "dtlBInfo", "OnSelect", MORE)
set_prop(t, "dtlBView", "OnSelect", f"Launch({doc_link()})")
set_prop(t, "dtlBSend", "OnSelect", SEND)
set_prop(t, "dtlLibView", "OnSelect", "Launch(ThisItem.Link)")
set_prop(t, "dtlLibSend", "OnSelect", LIBSEND)
set_prop(t, "dtlLibChg", "OnSelect", 'Set(varModalFile, ThisItem.Title); Set(varModalDocId, ThisItem.ID); Set(varModal, "aonChg")')
set_prop(t, "mAonSend", "OnSelect", AON)
set_prop(t, "mChgSend", "OnSelect", CHG)
set_prop(t, "mUplGo", "OnSelect", UPL)
set_prop(t, "mRectSend", "OnSelect", RECT)
set_prop(t, "mUplB", "Text", '"Attach the PDF received from AON to this request in SharePoint (open the request item and select Attach files), then select Upload. It is filed in the COI library."')
set_prop(t, "dtlDcV", "Text", "Text(ThisItem.Version)")
insert_after(t, "dtlTop", msg_label("dtlMsg", '=If(varLoading, "Loading...", varLoadError)', "varLoading || !IsBlank(varLoadError)", 12, color="ColorError", bold=True))
for c, p, ids in [("dtlId", "Text", "AC-REV-01.1 AC-REV-01.5"), ("dtlNote", "Text", "AC-RESUB-01.2"), ("dtlEdit", "OnSelect", "AC-RESUB-01.5"),
                  ("dtlKIdV", "Text", "AC-MYREQ-01.3"), ("galCovDet", "Items", "AC-REV-01.1"), ("txtTN", "HintText", "AC-REV-01.3"), ("dtlBSearch", "OnSelect", "AC-LIB-01.1"),
                  ("dtlBNewAon", "OnSelect", "AC-AON-01.1"), ("dtlBUpl", "OnSelect", "AC-RCV-02.1"), ("dtlBView", "OnSelect", "AC-RCV-01.1"),
                  ("dtlBRect", "OnSelect", "AC-RECT-01.1"), ("dtlMsgWait", "Text", "AC-REV-01.4"), ("dtlMsgDone", "Text", "AC-SEND-01.4"), ("galLib", "Items", "AC-LIB-01.1 AC-LIB-01.2"),
                  ("dtlLibChg", "OnSelect", "AC-LIB-01.5"), ("galDocs", "Items", "AC-REV-01.2"), ("galAct", "Items", "proposed change ACT-01 - see specs/acceptance-criteria/proposed-changes-2026-10-20.md"),
                  ("mAonB", "Text", "AC-AON-01.1"), ("txtRect", "Default", "AC-RECT-01.1")]:
    comment(t, c, p, ids)
detail = NL.join(t)

# ---- scrDocuments
g = to_lines(convert("scrDocuments"))
set_screen_prop(g, "OnVisible", "If(!varIsTreasury, Navigate(scrDashboard, ScreenTransition.None));" + NL + loaded(RELOAD))
set_prop(g, "docView", "OnSelect", "Launch(ThisItem.Link)")
for c, p, ids in [("galAllDocs", "Items", "AC-DOC-01.1 AC-DOC-01.2"), ("docView", "OnSelect", "AC-DOC-01.3")]:
    comment(g, c, p, ids)
docs = NL.join(g)

# ---------------------------------------------------------------- App.pa.yaml
app = (SRC / "App.pa.yaml").read_text(encoding="utf-8")
tokens = app.split("    Formulas: |-" + NL, 1)[1].split("      // AC-SOL-01.1")[0]
tokens = re.sub(r"      ColorPrimaryHover = [^;]*;", "      ColorPrimaryHover = RGBA(16, 94, 165, 1);", tokens)
tokens = re.sub(r"      ColorPrimaryPressed = [^;]*;", "      ColorPrimaryPressed = RGBA(12, 76, 134, 1);", tokens)
tokens = re.sub(r"      ColorTextMuted = [^;]*;", "      ColorTextMuted = RGBA(96, 94, 92, 1);", tokens)
tokens = re.sub(r"      ColorOverlay = [^;]*;", "      ColorOverlay = RGBA(0, 0, 0, 0.45);", tokens)
if "ColorDisabled" not in tokens:
    tokens += NEW_TOKENS
app_new = ("App:" + NL + "  Properties:" + NL + "    Formulas: |-" + NL + tokens +
           "      // AC-SOL-01.1 AC-SOL-01.2 Microsoft 365 and Power Platform only - the prototype is a reference, not shipped code" + NL +
           "      // AC-DEP-01.1 AC-DEP-01.3 UAT, deployment and handover are delivery activities - see specs/release-notes.md" + NL +
           "    OnStart: |-" + NL +
           "      =Set(varMyName, User().FullName);" + NL +
           "      Set(varIsTreasury, !IsBlank(LookUp(PRJ_TreasuryContact, ContactEmail = User().Email && IsActive = true))); // AC-ACC-01.3 shapes the UI only, list permissions are the control" + NL +
           '      Set(varEditing, false);' + NL + '      Set(varLang, "English");' + NL + '      Set(varWos, "Yes");' + NL + '      Set(varModal, "");' + NL +
           "      Set(varShowLib, false);" + NL + "      Set(varLoading, false);" + NL + '      Set(varLoadError, "");' + NL + "      Set(varSaving, false);" + NL +
           '      ClearCollect(colStatusFilter, {Value: "All"}, {Value: "Treasury Review"}, {Value: "Information Required"}, {Value: "Awaiting AON"}, {Value: "COI Received"}, {Value: "Awaiting AON Rectification"}, {Value: "Completed"});' + NL +
           '      ClearCollect(colCoverageNames, ForAll(SortByColumns(Filter(PRJ_CoverageType, IsActive = true), "SortOrder", SortOrder.Ascending), {N: Title})) // AC-REQ-02.1' + NL +
           "    Theme: =PowerAppsTheme" + NL)
(SRC / "App.pa.yaml").write_text(app_new, encoding="utf-8")
for n, tx in (("scrDashboard", dash), ("scrForm", form), ("scrDetail", detail), ("scrDocuments", docs)):
    (SRC / f"{n}.pa.yaml").write_text(tx.rstrip() + NL, encoding="utf-8")
(SRC / "_EditorState.pa.yaml").write_text("EditorState:" + NL + "  ScreensOrder:" + NL + "".join(f"    - {n}" + NL for n in ("scrDashboard", "scrForm", "scrDetail", "scrDocuments")), encoding="utf-8")
print("cloned")
