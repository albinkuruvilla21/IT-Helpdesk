"""Tests for prototype fidelity: tools/prototype_design.py (measuring the prototype) and the canvas_ui.py patterns that reproduce it.

    uv run python -m unittest discover -s tools/tests -v

Each pattern is checked the way pp.py build checks an app: every property against Studio's control templates, every formula with the
Power Fx checks (Microsoft's parser when pac is installed). What only Studio can show (the SVG drawn, the translucency) is spike S-UI.
"""
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import canvas_ui as ui  # noqa: E402
import pp  # noqa: E402
import prototype_design as pd  # noqa: E402
from test_powerfx import codes, run  # noqa: E402

TOKENS = ("IsDark = false;\nColorText = RGBA(0, 0, 0, 1);\nColorTextMuted = RGBA(0, 0, 0, 1);\nColorGlass = RGBA(255, 255, 255, 0.58);\n"
          "ColorGlassStroke = RGBA(255, 255, 255, 0.75);\nColorSegment = RGBA(0, 0, 0, 0.1);\nColorSegmentOn = RGBA(255, 255, 255, 1);\n"
          "ColorTransparent = RGBA(0, 0, 0, 0);\nColorHoverOverlay = RGBA(0, 0, 0, 0.06);\nColorPressedOverlay = RGBA(0, 0, 0, 0.12);\n"
          "ColorBorder = RGBA(0, 0, 0, 1);\nColorDivider = RGBA(0, 0, 0, 0.1);\nColorDisabled = RGBA(0, 0, 0, 1);\nColorSurface = RGBA(255, 255, 255, 1);\n"
          "ColorBackground = RGBA(255, 255, 255, 1);\nHexPrimary = \"#0a64d6\";\nHexSegment = \"#eeeeee\";\nHexText = \"#1d1d1f\";\nHexBackground = \"#eef0f6\";\n"
          "FontBody = Font.'Segoe UI';\nAppTitle = \"T\";")


def all_nodes(nodes):
    return list(ui._walk(nodes))


def unknown_properties(nodes):
    known, _ = pp.control_template_index({})
    bad = []
    for n in all_nodes(nodes):
        allowed = known.get(pp.template_key(n.control))
        if allowed is None:
            bad.append((n.name, n.control, "no template"))
            continue
        bad += [(n.name, n.control, k) for k in n.props if k not in allowed and k not in pp.CONTAINER_CHILD_PROPS]
    return bad


class Measure(unittest.TestCase):
    def test_selftest(self):
        pd.selftest()

    def test_dark_scheme_and_contrast_fix(self):
        d = pd.extract(pd.SELFTEST_HTML, 1060)
        self.assertTrue(d["has_dark_scheme"])
        fail = [c for c in d["contrast"] if not c["pass"]]
        self.assertTrue(fail, "the muted grey fails on the page background in the sample")
        for c in fail:
            self.assertGreaterEqual(pd.contrast(pd.color(c["compliant"]), pd.color(c["bg"])), 4.5)

    def test_px_to_points(self):
        self.assertEqual(pd.to_pt(32), 24)
        self.assertEqual(ui.Design(1020 / 1060).pt(32), 23)
        self.assertEqual(ui.Design(1.0).h(15, 1.47), 22)

    def test_check_app_both_ways(self):
        d = pd.extract(pd.SELFTEST_HTML, 1060)
        good = "\n".join("      " + x for x in pd.formulas(d))
        self.assertEqual(pd.check_app(d, good), ([], []))
        missing = "\n".join(line for line in good.split("\n") if "ColorPrimary =" not in line and "IsDark =" not in line)
        errors, _ = pd.check_app(d, missing)
        self.assertEqual(len(errors), 2, errors)  # no IsDark, no ColorPrimary
        changed = good.replace("RGBA(29, 29, 31, 1)", "RGBA(0, 0, 0, 1)")
        self.assertEqual(len(pd.check_app(d, changed)[1]), 1)

    def test_real_prototype_if_present(self):
        found = sorted((TOOLS.parent / "inputs" / "design").glob("*.html"))
        if not found:
            self.skipTest("no HTML prototype in inputs/design")
        d = pd.extract(found[0].read_text(encoding="utf-8"), 1020)
        self.assertIn("ColorPrimary", d["tokens"])
        # whichever prototype the project holds: the measure must find a type scale whose sizes convert to points and label heights
        self.assertTrue(d["type_scale"])
        self.assertTrue(all(t["pt"] > 0 and t["label_h"] > 0 for t in d["type_scale"]), d["type_scale"][:3])


class Patterns(unittest.TestCase):
    GEO = {"w": 1020, "top": 12, "h": 46, "radius": 23, "pad": 13, "title_pt": 12.5, "tab_h": 29, "tab_pt": 10, "seg_pad": 3, "user_pt": 9.5}

    def bar(self):
        return ui.floating_topbar("dsh", "=AppTitle", 'User().FullName', [("Dashboard", "scrA", None, 90), ("Approvals", "scrA", "true", 90)], 0, self.GEO,
                                  logo={"size": 25, "radius": 8, "from": "HexPrimary", "to": "HexText"})

    def test_properties_are_studios(self):
        nodes = self.bar() + [ui.svg_ring("imgRing", "34", 84, 9, "HexSegment", "HexPrimary", "HexText", "HexText", 9.5),
                              ui.svg_backdrop("imgBack", "HexBackground", [(0.12, 0.08, 0.55, "HexPrimary")]),
                              ui.box("boxGlass", [], radius=23, fill="ColorGlass", border=True, border_color="ColorGlassStroke", shadow="Light"),
                              ui.button("btnPill", "Go", "Notify(\"x\")", "primary", radius="pill")]
        self.assertEqual(unknown_properties(nodes), [])

    def test_formulas_pass_the_checks(self):
        nodes = self.bar() + [ui.svg_ring("imgRing", "34", 84, 9, "HexSegment", "HexPrimary", "HexText", "HexText", 9.5),
                              ui.svg_backdrop("imgBack", "HexBackground", [(0.12, 0.08, 0.55, "HexPrimary")])]
        res = run(controls=nodes, formulas=TOKENS, screens={"scrA": nodes})
        self.assertEqual(codes(res, "error"), [], [f.message for f in res.findings if f.severity == "error"])

    def test_no_colour_literal_on_a_screen(self):
        y = "\n".join(str(v) for n in all_nodes(self.bar()) for v in n.props.values())
        self.assertNotRegex(y, r"RGBA\(|#[0-9A-Fa-f]{6}\b")

    def test_tab_positions_skip_hidden_tabs(self):
        tabs = {n.name: n for n in self.bar()}
        self.assertIn("If(true, 90 + 2, 0)", tabs["dshHdrSeg"].props["Width"])
        self.assertTrue(tabs["dshTab2"].props["X"].endswith("+ 92"))

    def test_tokens_block_dark(self):
        block = ui.tokens_block({"ColorText": "RGBA(29, 29, 31, 1)"}, dark={"ColorText": "RGBA(245, 245, 247, 1)"}, hexes={"ColorPrimary": ("#0a64d6", "#409cff")})
        self.assertIn("IsDark = Coalesce(First(colScheme).Value, \"Light\") = \"Dark\";", block)
        self.assertIn("ColorText = If(IsDark, RGBA(245, 245, 247, 1), RGBA(29, 29, 31, 1));", block)
        self.assertIn('HexPrimary = If(IsDark, "#409cff", "#0a64d6");', block)
        self.assertNotIn("IsDark", ui.tokens_block())  # unchanged without a dark scheme


if __name__ == "__main__":
    unittest.main()
