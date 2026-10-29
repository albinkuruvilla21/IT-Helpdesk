"""Tests for tools/powerfx.py (the formula checks `pp.py build` and `pp.py fx` run).

    uv run python -m unittest discover -s tools/tests -v

Each rule is tested both ways: it fires on a defect and stays quiet on the correct formula. The parser is cross-checked against
Microsoft's (pac's Microsoft.PowerFx.Core) when pac and PowerShell 7 are installed; those tests are skipped, and say so, otherwise.
The corpus tests run the checks over the Studio-built sample app, which Studio opened and saved: any syntax, function, arity,
behaviour, name, property or enumeration finding there is a defect in the checker, not in the app.
"""
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import canvas_ui  # noqa: E402
import powerfx as fx  # noqa: E402
import pp  # noqa: E402

LABEL = "Label@2.5.1"
BUTTON = "Classic/Button@2.2.0"
GALLERY = "Gallery@2.15.0"
FORM = "Form@2.4.4"
INPUT = "Classic/TextInput@2.3.2"

TOKENS = "ColorText = RGBA(0, 0, 0, 1);\nAppTitle = \"T\";\nIsAdmin = User().Email = \"\";"


def schema():
    C = fx.Column
    cols = [C(k, k, t, False, ix, ro) for k, (t, ro, ix) in fx.SP_SYSTEM.items()]
    cols += [C("Status", "Status", "Choice", indexed=True, choices=["Open", "Closed"]), C("Notes", "Notes", "Note"),
             C("Owner", "Owner", "User"), C("Amount", "Amount", "Number", indexed=True), C("Region", "Region", "Text"),
             C("Code", "Code", "Text", required=True, indexed=True), C("DueDate", "Due Date", "DateTime", indexed=True)]
    return {"CON_Request": fx.ListSchema("CON_Request", cols)}


FLOWS = {"Request - Notify approver": {"kind": "PowerAppV2", "params": ["text", "text_1"], "required": ["text"]},
         "Legacy flow": {"kind": "PowerApp", "params": None, "required": []}}


def screen_yaml(name, controls, props=None):
    lines = ["Screens:", f"  {name}:", "    Properties:"]
    for k, v in (props or {"Fill": "=ColorText"}).items():
        lines.append(f"      {k}: {canvas_ui._q(canvas_ui._eq(v))}")
    if controls:
        lines.append("    Children:")
        for c in controls:
            lines += canvas_ui.emit(c, 6)
    return "\n".join(lines) + "\n"


def app_yaml(formulas=TOKENS, props=None):
    body = "\n".join("      " + ln for ln in ("=" + formulas).split("\n"))
    extra = "".join(f"    {k}: {canvas_ui._q(canvas_ui._eq(v))}\n" for k, v in (props or {}).items())
    return f"App:\n  Properties:\n    Formulas: |-\n{body}\n{extra}"


def ctl(name, ctype, children=None, variant=None, **props):
    return canvas_ui.Node(name, ctype, props, children, variant)


def run(controls=(), screens=None, formulas=TOKENS, app_props=None, release=False, official=False, datasources=(), screen_props=None):
    texts = {"Src/App.pa.yaml": app_yaml(formulas, app_props)}
    for sname, ctls in (screens or {"scrA": list(controls)}).items():
        texts[f"Src/{sname}.pa.yaml"] = screen_yaml(sname, ctls, screen_props)
    kw = pp.formula_check_args({}, list(datasources))
    return fx.check_app("test", texts, schemas=schema(), flows=FLOWS, prefix="CON", release=release, use_official=official, **kw)


def codes(res, severity=None):
    return sorted({f.code for f in res.findings if severity is None or f.severity == severity})


def button(onselect, name="btnGo", **kw):
    return ctl(name, BUTTON, OnSelect=onselect, Text='="Go"', **kw)


def label(text, name="lblA", **kw):
    return ctl(name, LABEL, Text=text, **kw)


class SplitColumn(unittest.TestCase):
    """PA-T38: Studio refused `Trim(Result)` over a Split table (Name isn't valid. 'Result' isn't recognized)."""

    def test_result_column_is_refused(self):
        bad = 'Set(isAdmin, !IsBlank(LookUp(Split("a;b", ";"), Trim(Result) = "a")))'
        self.assertIn("FX-NAME", codes(run(formulas=TOKENS, controls=[button(bad)]), "error"))

    def test_in_over_the_split_table_is_accepted(self):
        good = 'Set(isAdmin, "a" in Split(Substitute("a; b", " ", ""), ";"))'
        self.assertNotIn("FX-NAME", codes(run(formulas=TOKENS, controls=[button(good)]), "error"))


class Parsing(unittest.TestCase):
    VALID = [
        'Notify("Hello " & AppTitle, NotificationType.Success)', "Set(a, 1); Set(b, {x: 1, 'y z': [1, 2]})", '$"Hi {User().FullName}!"',
        "Filter(T As r, r.A = 1 && !IsBlank(r.B))", "[@colItems]", "colItems[@Value]", "50%", "-x ^ 2", "a in b", "a exactin b",
        "If(x, Set(a, 1); Navigate(scr), Back())", "'My List'.'Col Name'", "Parent.Width - 440", "1.5e3", ".5", "",
        "x // comment", "/* c */ x", "{}", "[]", "Not x", "Not(x)", "a And b Or c", 'Text(Now(), "yyyy-mm-dd")', "Set(a, 1);",
        '$"{{literal}} {1 + 2} ""q"""', "ForAll(Sequence(3), Value)",
    ]
    INVALID = ["If(a, b", "Notify(\"x)", "f(1,,2)", "a +", "(a)(1)", "{a 1}", "[1, 2", "'unclosed", "/* x", "x.", "Set(a,)",
               "\u201chello\u201d"]

    def test_valid(self):
        for src in self.VALID:
            with self.subTest(src=src):
                fx.parse(src)

    def test_invalid(self):
        for src in self.INVALID:
            with self.subTest(src=src):
                with self.assertRaises(fx.FxSyntaxError):
                    fx.parse(src)

    def test_named_formulas_and_udfs(self):
        p = fx.Parser('A = 1;\nB(x: Number, y: Text): Number = x + 1;\nGo(): Void = { Set(a, 1); Notify("x") };\nC := Type({a: Number});')
        e = p.named_formulas()
        self.assertEqual([x["name"] for x in e], ["A", "B", "Go", "C"])
        self.assertEqual(e[1]["params"], ["x", "y"])
        self.assertTrue(e[2]["behavior"])
        self.assertFalse(e[1]["behavior"])

    def test_agrees_with_microsoft(self):
        items = [(f"v{i}", s, True) for i, s in enumerate(self.VALID)] + [(f"i{i}", s, True) for i, s in enumerate(self.INVALID)]
        res, info = fx.official_parse(items)
        if res is None:
            self.skipTest(f"Microsoft's parser not available: {info}")
        for id_, src, _ in items:
            with self.subTest(src=src):
                self.assertEqual(res[id_]["ok"], id_.startswith("v"), res[id_]["errors"])

    def test_microsoft_rejects_chaining_in_data_property(self):
        res, info = fx.official_parse([("d", "Set(a, 1); Back()", False), ("b", "Set(a, 1); Back()", True)])
        if res is None:
            self.skipTest(f"Microsoft's parser not available: {info}")
        self.assertFalse(res["d"]["ok"])
        self.assertTrue(res["b"]["ok"])


class Yaml(unittest.TestCase):
    def test_scalars_and_lines(self):
        doc = fx.load_yaml("A:\n  P1: =x # yaml comment\n  P2: '=\"a: b\" // c'\n  P3: |-\n    =If(a,\n      b)\n  P4: =\"it''s\"\n")
        self.assertEqual(doc["A"]["P1"].text, "=x")
        self.assertEqual(doc["A"]["P2"].text, '="a: b" // c')
        self.assertEqual(doc["A"]["P3"].text, "=If(a,\n  b)")
        self.assertEqual(doc["A"]["P3"].line, 5)
        self.assertEqual(doc["A"]["P4"].text, "=\"it''s\"")

    def test_yaml_comment_truncates_formula(self):
        res = fx.check_app("t", {"Src/scrA.pa.yaml": "Screens:\n  scrA:\n    Children:\n      - lblA:\n          Control: Label@2.5.1\n"
                                                    "          Properties:\n            Text: =\"Item #1\"\n"},
                           schemas={}, flows={}, prefix=None, use_official=False)
        self.assertIn("FX-SYNTAX", codes(res, "error"))

    def test_value_without_equals(self):
        res = fx.check_app("t", {"Src/scrA.pa.yaml": "Screens:\n  scrA:\n    Properties:\n      Fill: ColorText\n"},
                           schemas={}, flows={}, prefix=None, use_official=False)
        self.assertIn("FX-YAML", codes(res, "error"))


class Rules(unittest.TestCase):
    def assertFires(self, res, code, severity="error"):
        self.assertIn(code, codes(res, severity), "\n".join(f.text() for f in res.findings))

    def assertQuiet(self, res, code=None):
        found = [f for f in res.findings if code is None or f.code == code]
        self.assertFalse(found, "\n".join(f.text() for f in found))

    def test_clean_screen(self):
        self.assertQuiet(run([label("=AppTitle"), button('Notify("Saved", NotificationType.Success) // AC-CON-01.1')]))

    def test_unknown_function_and_case(self):
        self.assertFires(run([button("Notfy(\"x\")")]), "FX-FUNC")
        res = run([button('notify("x")')])
        self.assertTrue(any("did you mean Notify" in f.message for f in res.findings))

    def test_arity(self):
        self.assertFires(run([button("Set(a)")]), "FX-ARITY")
        self.assertFires(run([label("=Left(\"abc\")")]), "FX-ARITY")
        self.assertQuiet(run([label('=Left("abc", 1)')]), "FX-ARITY")

    def test_behavior_in_data_property(self):
        self.assertFires(run([label('=Set(a, 1)')]), "FX-BEHAVIOR")
        self.assertFires(run([label('="x"')], formulas=TOKENS + "\nBad = Navigate(scrA);"), "FX-BEHAVIOR")
        self.assertQuiet(run([button("Set(a, 1); Navigate(scrA)"), label("=a")]), "FX-BEHAVIOR")

    def test_behavior_udf(self):
        f = TOKENS + '\nSaveIt(): Void = { Set(a, 1); Notify("x") };'
        self.assertQuiet(run([button("SaveIt()"), label("=a")], formulas=f))
        self.assertFires(run([label("=SaveIt()"), button("Set(a, 1)", name="b2"), label("=a", name="l2")], formulas=f), "FX-BEHAVIOR")

    def test_chaining_in_data_property(self):
        self.assertFires(run([label('="a"; "b"')]), "FX-SYNTAX")

    def test_unknown_name(self):
        self.assertFires(run([label("=varNope")]), "FX-NAME")
        self.assertFires(run([label("=apptitle")]), "FX-NAME")
        self.assertFires(run([label("=CON_Missing")]), "FX-SCHEMA")

    def test_context_variable_is_per_screen(self):
        res = run(screens={"scrA": [button("UpdateContext({locX: 1})"), label("=Text(locX)")],
                           "scrB": [label("=Text(locX)", name="lblB")]})
        bad = [f for f in res.findings if f.code == "FX-NAME"]
        self.assertEqual(len(bad), 1, [f.text() for f in res.findings])
        self.assertIn("scrA", bad[0].message)

    def test_navigate_context(self):
        res = run(screens={"scrA": [button("Navigate(scrB, ScreenTransition.None, {locId: 3})")], "scrB": [label("=Text(locId)", name="lblB")]})
        self.assertQuiet(res, "FX-NAME")
        self.assertFires(run([button("Navigate(scrNope)")]), "FX-NAME")

    def test_control_property(self):
        res = run([ctl("txtName", INPUT, Default='=""'), label("=txtName.Value")])
        self.assertFires(res, "FX-CTRLPROP")
        self.assertQuiet(run([ctl("txtName", INPUT, Default='=""'), label("=txtName.Text")]), "FX-CTRLPROP")
        self.assertFires(run([label("=Self.Txt")]), "FX-CTRLPROP")

    def test_this_item(self):
        self.assertFires(run([label("=ThisItem.Title")]), "FX-THISITEM")
        gal = ctl("galReq", GALLERY, [label("=ThisItem.Title", name="lblT")], variant="Vertical", Items="=CON_Request")
        self.assertQuiet(run([gal]))
        gal = ctl("galReq", GALLERY, [label("=ThisItem.Nope", name="lblT")], variant="Vertical", Items="=CON_Request")
        self.assertFires(run([gal]), "FX-SCHEMA")

    def test_enums(self):
        self.assertFires(run([button("Notify(\"x\", NotificationType.Danger)")]), "FX-ENUM")
        self.assertFires(run([button("Notify(\"x\", \"Error\")")]), "FX-ENUM")
        self.assertFires(run([button("Navigate(scrA, NotificationType.Error)")]), "FX-ENUM")

    def test_literal_types(self):
        self.assertFires(run([label('="x"', Align='="Center"')]), "FX-TYPE")
        self.assertFires(run([label('="x"', Width='="wide"')]), "FX-TYPE")
        self.assertFires(run([label('="x"', Color='="red"')]), "FX-TYPE")
        self.assertFires(run([label('="x"', Visible='="maybe"')]), "FX-TYPE")
        self.assertFires(run([label('="x"', Width='="40"')]), "FX-TYPE", "warning")
        self.assertQuiet(run([label('="x"', Align="=Align.Center", Width="=40", Visible="=true")]), "FX-TYPE")

    def test_text_that_should_be_a_formula(self):
        self.assertFires(run([label('="User().FullName"')]), "FX-TEXT", "warning")
        self.assertFires(run([label('=""""')]), "FX-TEXT", "warning")
        self.assertQuiet(run([label('="Hello (world)."')]), "FX-TEXT")

    def test_patch_columns_and_types(self):
        ok = 'IfError(Patch(CON_Request, Defaults(CON_Request), {Code: "A1", Status: {Value: "Open"}, Amount: 3}), Notify("Not saved", NotificationType.Error))'
        self.assertQuiet(run([button(ok)]))
        self.assertFires(run([button(ok.replace("Amount: 3", "Nope: 3"))]), "FX-SCHEMA")
        self.assertFires(run([button(ok.replace('Status: {Value: "Open"}', 'Status: "Open"'))]), "FX-PATCH")
        self.assertFires(run([button(ok.replace('{Value: "Open"}', '{Value: "Pending"}'))]), "FX-PATCH")
        self.assertFires(run([button(ok.replace("Amount: 3", 'Amount: "three"'))]), "FX-PATCH")
        self.assertFires(run([button(ok.replace("Amount: 3", "Created: Now()"))]), "FX-PATCH")
        self.assertFires(run([button(ok.replace("Defaults(CON_Request)", "Defaults(colX)"))]), "FX-PATCH")
        self.assertFires(run([button(ok.replace('Code: "A1", ', ""))]), "FX-PATCH", "warning")
        self.assertQuiet(run([button(ok.replace("Amount: 3", "'Due Date': Today()"))]))

    def test_first_error_scope(self):
        inside = 'IfError(Patch(CON_Request, Defaults(CON_Request), {Code: "A"}), Notify(FirstError.Message, NotificationType.Error))'
        self.assertQuiet(run([button(inside)]), "FX-NAME")
        self.assertFires(run([button('Notify(FirstError.Message, NotificationType.Error)')]), "FX-NAME")
        self.assertQuiet(run([button('Notify("x")')], app_props={"OnError": 'Notify(FirstError.Message, NotificationType.Error)'}), "FX-NAME")

    def test_navigate_not_in_onvisible(self):
        self.assertFires(run([], screens={"scrA": [], "scrB": []}, screen_props={"Fill": "=ColorText", "OnVisible": "=Navigate(scrB, ScreenTransition.None)"}), "FX-NAV")
        self.assertFires(run([], screens={"scrA": [], "scrB": []}, screen_props={"Fill": "=ColorText", "OnVisible": "=If(true, Navigate(scrB, ScreenTransition.None))"}), "FX-NAV")
        self.assertQuiet(run([button("Navigate(scrA, ScreenTransition.None)")]), "FX-BEHAVIOR")

    def test_iferror_types_match(self):
        bad = 'IfError(ClearCollect(colX, {a: 1}), Notify("x", NotificationType.Error))'
        self.assertFires(run([button(bad)]), "FX-TYPE")
        self.assertQuiet(run([button('IfError(ClearCollect(colX, {a: 1}); true, Notify("x", NotificationType.Error))')]), "FX-TYPE")
        self.assertQuiet(run([button('IfError(Notify("a"), Notify("x", NotificationType.Error))')]), "FX-TYPE")

    def test_studio_rejections_from_the_first_open(self):
        self.assertFires(run([button('IfError(Notify("a"), Notify(If(FirstError.Kind = ErrorKind.EditPermission, "x", "y")))')]), "FX-ENUM")
        self.assertQuiet(run([button('IfError(Notify("a"), Notify(If(FirstError.Kind = ErrorKind.ReadPermission, "x", "y")))')]), "FX-ENUM")
        self.assertFires(run([button('ClearCollect(colS, ShowColumns(CON_Request, "Code", "Status"))')]), "FX-ARG")
        self.assertQuiet(run([button("ClearCollect(colS, ShowColumns(CON_Request, Code, Status))")]), "FX-ARG")
        dd = lambda d: ctl("drpP", "ModernDropdown@1.0.3", Items="=colP", Default=d, ItemDisplayText="=ThisItem.Value")  # noqa: E731
        self.assertFires(run([dd("=varForm.Project")]), "FX-TYPE")
        self.assertQuiet(run([dd("=LookUp(colP, Value = varP)")]), "FX-TYPE")

    def test_write_error_handling(self):
        self.assertFires(run([button('Patch(CON_Request, Defaults(CON_Request), {Code: "A"})')]), "FX-ERRHANDLING", "warning")
        self.assertQuiet(run([button('Patch(CON_Request, Defaults(CON_Request), {Code: "A"})')],
                             app_props={"OnError": 'Notify(FirstError.Message, NotificationType.Error)'}), "FX-ERRHANDLING")

    def test_delegation(self):
        def items(expr):
            return run([ctl("galReq", GALLERY, [label("=ThisItem.Title", name="lblT")], variant="Vertical", Items=expr)])
        self.assertQuiet(items('=Filter(CON_Request, Status.Value = "Open" && StartsWith(Code, txtQ.Text))'.replace("txtQ.Text", '"A"')))
        self.assertFires(items('=Filter(CON_Request, Lower(Code) = "a")'), "FX-DELEG")
        self.assertFires(items('=Filter(CON_Request, "a" in Code)'), "FX-DELEG")
        self.assertFires(items('=Search(CON_Request, "a", Code)'), "FX-DELEG")
        self.assertFires(items('=Filter(CON_Request, Notes = "a")'), "FX-DELEG")
        self.assertFires(items('=Sort(CON_Request, Len(Code))'), "FX-DELEG")
        self.assertQuiet(items('=SortByColumns(Filter(CON_Request, Amount > 3), "DueDate", SortOrder.Descending)'))
        res = run([label("=Text(CountRows(CON_Request))")])
        self.assertFires(res, "FX-DELEG", "warning")

    def test_index(self):
        self.assertFires(run([label('=LookUp(CON_Request, Region = "EU").Title')]), "FX-INDEX")
        self.assertQuiet(run([label('=LookUp(CON_Request, ID = 3).Title')]), "FX-INDEX")
        self.assertFires(run([label('=First(SortByColumns(CON_Request, "Region")).Title')]), "FX-INDEX")

    def test_variables(self):
        res = run([button("Set(gblX, 1)"), button('Set(gblX, "one")', name="b2"), label("=Text(gblX)")])
        self.assertFires(res, "FX-VAR")
        self.assertFires(run([button("Set(AppTitle, 1)")]), "FX-VAR")
        self.assertFires(run([button("Set(gblY, 1)")]), "FX-UNUSED", "warning")
        self.assertFires(run([button("UpdateContext(locX)")]), "FX-VAR")

    def test_flows(self):
        self.assertQuiet(run([button("'Request - Notify approver'.Run(\"a\")")]), "FX-FLOW")
        self.assertFires(run([button("'No such flow'.Run()")]), "FX-FLOW")
        self.assertFires(run([button("'Request - Notify approver'.Run()")]), "FX-FLOW")
        self.assertFires(run([button("'Request - Notify approver'.Run(\"a\", \"b\", \"c\")")]), "FX-FLOW")
        self.assertFires(run([label("='Legacy flow'.Run()")]), "FX-BEHAVIOR")

    def test_ac_comments(self):
        self.assertFires(run([button('Notify("x") // AC-CON-01')]), "FX-AC", "warning")
        self.assertFires(run([label('="Welcome // AC-CON-01.1"')]), "FX-AC")
        self.assertFires(run([button("// AC-CON-01.1")]), "FX-AC")
        self.assertFires(run([button('Notify("x") // TODO(AC-CON-01.2)')]), "FX-AC", "warning")
        self.assertFires(run([button('Notify("x") // TODO(AC-CON-01.2)')], release=True), "FX-AC")
        self.assertQuiet(run([button('Notify("x") // AC-CON-01.2')]), "FX-AC")

    def test_ac_project_code_ids(self):
        # AC-<PROJECT>-NN: a project code of up to 10 letters and digits is a valid ID (acceptance-criteria-standard §3).
        self.assertQuiet(run([button('Notify("x") // AC-TIMESMOD-12.3')]), "FX-AC")
        self.assertFires(run([button('Notify("x") // AC-TIMESMOD-12')]), "FX-AC", "warning")
        self.assertFires(run([label('="Due // AC-TIMESMOD-12.3"')]), "FX-AC")
        # Longer than 10 is not an ID, so the traceability check could not see it.
        self.assertFires(run([button('Notify("x") // AC-ABCDEFGHIJK-01.1')]), "FX-AC", "warning")

    def test_tokens(self):
        self.assertFires(run([label('="x"', Color="=RGBA(1, 2, 3, 1)")]), "FX-TOKEN")

    def test_duplicate_name_across_screens(self):
        self.assertFires(run(screens={"scrA": [label("=AppTitle")], "scrB": [label("=AppTitle")]}), "FX-DUPNAME")

    def test_overlay_control_without_visible(self):
        # a dialog's controls are placed from its panel; one with no Visible of its own shows on every screen (PA-T41)
        panel = ctl("pnDlg", "GroupContainer@1.5.0", variant="ManualLayout", Visible='=varModal = "x"', X="=0", Y="=0", Width="=100", Height="=100")
        shown = ctl("ddOne", "ModernDropdown@1.0.3", Items="=[1]", X="=pnDlg.X + 20", Y="=pnDlg.Y + 20", Visible='=varModal = "x"')
        hidden = ctl("ddTwo", "ModernDropdown@1.0.3", Items="=[1]", X="=pnDlg.X + 20", Y="=pnDlg.Y + 60")
        self.assertQuiet(run([panel, shown]), "FX-OVERLAY")
        self.assertFires(run([panel, shown, hidden]), "FX-OVERLAY")

    def test_svg_number_format_leaves_a_trailing_separator(self):
        bad = '="<svg><rect width=\'" & Text(20 * 150 / 100, "0.##") & "\'/></svg>"'
        good = '="<svg><rect width=\'" & Substitute(Text(Round(20 * 150 / 100, 1)), ",", ".") & "\'/></svg>"'
        self.assertFires(run([ctl("imgA", "Image@2.2.3", Image=bad)]), "FX-SVG")
        self.assertQuiet(run([ctl("imgA", "Image@2.2.3", Image=good)]), "FX-SVG")
        self.assertQuiet(run([label('=Text(Today(), "dd mmm yyyy")')]), "FX-SVG")

    def test_attachments_table_has_no_name_column(self):
        bad = "=ForAll(LookUp(CON_Request, ID = 1).Attachments, {Name: Name})"
        good = "=ForAll(LookUp(CON_Request, ID = 1).Attachments, {Name: DisplayName})"
        self.assertFires(run([ctl("galA", "Gallery@2.15.0", Items=bad)]), "FX-NAME")
        self.assertQuiet(run([ctl("galA", "Gallery@2.15.0", Items=good)]), "FX-NAME")

    def test_yaml_lint_accepts_a_bare_equals(self):
        # Studio itself writes an empty formula as `LayoutMaxHeight: =`; PyYAML resolves a bare `=` to a tag it cannot construct (PA1001 false alarm)
        ok = pp.Report("t")
        pp._lint_yaml_syntax(ok, "app", "Src/scrA.pa.yaml", "Screens:\n  scrA:\n    Children:\n      - a:\n          Properties:\n            LayoutMaxHeight: =\n")
        self.assertEqual(ok.errors, [], ok.errors)
        bad = pp.Report("t")
        pp._lint_yaml_syntax(bad, "app", "Src/scrA.pa.yaml", "Screens:\n  scrA:\n    Children:\n      - a: [\n")
        self.assertTrue(bad.errors)

    def test_named_formula_error_does_not_cascade(self):
        res = run([label("=AppTitle")], formulas=TOKENS + "\nBroken = If(1;")
        self.assertFires(res, "FX-SYNTAX")
        self.assertQuiet(res, "FX-NAME")  # AppTitle is still known

    def test_type_definition_not_analysed(self):
        self.assertQuiet(run([label("=AppTitle")], formulas=TOKENS + "\nPoint := Type({X: Number, Y: Number});"))

    def test_count_of_filtered_list(self):
        self.assertFires(run([label('=Text(CountRows(Filter(CON_Request, Amount > 3)))')]), "FX-DELEG", "warning")

    def test_text_expression_into_number_column(self):
        ok = 'IfError(Patch(CON_Request, Defaults(CON_Request), {Code: "A", Amount: "1" & "2"}), Notify("x", NotificationType.Error))'
        self.assertFires(run([button(ok)]), "FX-PATCH")

    def test_suppression(self):
        bad = '=Filter(CON_Request, "a" in Code) // fx-ignore FX-DELEG list capped at 300 items, agreed with PO 2026-10-26'
        gal = ctl("galReq", GALLERY, [label("=ThisItem.Title", name="lblT")], variant="Vertical", Items=bad)
        res = run([gal])
        self.assertQuiet(res, "FX-DELEG")
        self.assertTrue(res.suppressed)
        gal = ctl("galReq", GALLERY, [label("=ThisItem.Title", name="lblT")], variant="Vertical",
                  Items='=Filter(CON_Request, "a" in Code) // fx-ignore FX-DELEG ok')
        self.assertFires(run([gal]), "FX-IGNORE")
        self.assertFires(run([label('=Lft("a") // fx-ignore FX-FUNC because I said so today')]), "FX-IGNORE")


class Corpus(unittest.TestCase):
    STUDIO = {"FX-SYNTAX", "FX-FUNC", "FX-ARITY", "FX-BEHAVIOR", "FX-CTRLPROP", "FX-ENUM", "FX-PARSER", "FX-NAME", "FX-THISITEM",
              "FX-YAML", "FX-DUPNAME"}

    def load(self, folder: Path):
        texts = {f"Src/{p.name}": p.read_text(encoding="utf-8-sig") for p in sorted((folder / "Src").glob("*.pa.yaml"))}
        templates, datasources = pp.app_references(folder)
        return texts, pp.formula_check_args(templates, datasources)

    def test_studio_built_sample_has_no_studio_class_findings(self):
        texts, kw = self.load(TOOLS.parent / "samples" / "powerapp")
        res = fx.check_app("sample", texts, schemas={}, flows={}, prefix=None, **kw)
        wrong = [f.text() for f in res.findings if f.code in self.STUDIO]
        self.assertEqual(wrong, [], "the checker reports an error Studio did not")
        self.assertGreater(res.stats["formulas"], 3000)
        self.assertGreater(res.stats["calls"], 1000)

    def test_sample_property_checks_are_live(self):
        """Break one property reference in the sample: the control-property check must see it (it is not silently skipped)."""
        texts, kw = self.load(TOOLS.parent / "samples" / "powerapp")
        key = "Src/scrDocuments.pa.yaml"
        texts[key] = texts[key].replace("Parent.TemplateHeight", "Parent.TemplateHeigth", 1)
        res = fx.check_app("sample", texts, schemas={}, flows={}, prefix=None, use_official=False, **kw)
        self.assertIn("FX-CTRLPROP", codes(res, "error"))

    def test_starter_app_is_clean(self):
        """The project's own app has no errors. (The starter had no findings at all; a delivered app keeps judgement warnings such as an
        agreed fx-ignore, which are printed on every build, so only errors fail here.)"""
        cfg = pp.load_config()
        for app in cfg["canvasApps"]:
            texts, kw = self.load(TOOLS.parent / app["source"])
            res = fx.check_app(app["name"], texts, **kw)
            self.assertEqual([f.text() for f in res.findings if f.severity == "error"], [])


if __name__ == "__main__":
    unittest.main()
