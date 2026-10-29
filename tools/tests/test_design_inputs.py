"""Tests for the design inputs: tools/figma_pull.py measures a Figma node tree (offline), and tools/ingest.py reports a
prototype gap when the design can't be measured.

    uv run python -m unittest discover -s tools/tests -v
"""
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import figma_pull  # noqa: E402
import ingest  # noqa: E402

BLUE = {"r": 0, "g": 0.4, "b": 0.8, "a": 1}
FRAME = {
    "type": "FRAME", "name": "Home", "id": "1:2", "absoluteBoundingBox": {"x": 0, "y": 0, "width": 1440, "height": 900},
    "fills": [{"type": "SOLID", "color": BLUE}], "cornerRadius": 16, "layoutMode": "VERTICAL", "itemSpacing": 24,
    "paddingTop": 32, "paddingRight": 32, "paddingBottom": 32, "paddingLeft": 32,
    "effects": [{"type": "DROP_SHADOW", "offset": {"x": 0, "y": 4}, "radius": 12, "spread": 0, "color": {"r": 0, "g": 0, "b": 0, "a": 0.2}}],
    "children": [
        {"type": "TEXT", "name": "Title", "style": {"fontFamily": "Inter", "fontSize": 32, "lineHeightPx": 40, "fontWeight": 700}},
        {"type": "TEXT", "name": "Hidden", "visible": False, "style": {"fontFamily": "Inter", "fontSize": 99, "fontWeight": 400}},
    ],
}


def tally(scale):
    acc = {k: Counter() for k in ("fill", "stroke", "type", "radius", "effect", "gap", "padding")}
    figma_pull.walk(FRAME, acc, scale)
    return acc


class FigmaValuesTests(unittest.TestCase):
    def test_type_is_converted_to_points_at_the_scale(self):
        acc = tally(0.5)
        self.assertEqual(list(acc["type"]), ["Inter 32px = 12pt / line 20 w700"])  # 32 x 0.5 x 0.75 = 12

    def test_lengths_are_scaled(self):
        acc = tally(0.5)
        self.assertEqual(list(acc["radius"]), ["8"])
        self.assertEqual(list(acc["gap"]), ["12"])
        self.assertEqual(list(acc["padding"]), ["16 16 16 16"])
        self.assertEqual(list(acc["effect"]), ["drop_shadow 0 2 6 0 #000000 @0.2"])

    def test_colours_and_hidden_layers(self):
        acc = tally(1)
        self.assertEqual(list(acc["fill"]), ["#0066CC"])
        self.assertNotIn("99px", " ".join(acc["type"]))

    def test_screens_keep_phone_frames_but_not_parts(self):
        kids = [dict(FRAME, id="a", absoluteBoundingBox={"width": 390}), dict(FRAME, id="b", absoluteBoundingBox={"width": 120}),
                {"type": "GROUP", "id": "c", "absoluteBoundingBox": {"width": 1440}}]
        self.assertEqual([f["id"] for f in figma_pull.screens(kids, 320)], ["a"])

    def test_missing_config_says_what_to_write(self):
        old = figma_pull.CONFIG
        figma_pull.CONFIG = Path(tempfile.gettempdir()) / "no-such-dir" / "figma.json"
        try:
            with self.assertRaises(SystemExit) as e:
                figma_pull.config()
            self.assertIn("figma.json", str(e.exception.code))
        finally:
            figma_pull.CONFIG = old


class PrototypeGapTests(unittest.TestCase):
    def rows(self, *names):
        return [(f"design/{n}", Path(n), "x", None) for n in names]

    def setUp(self):
        self.root = ingest.ROOT
        ingest.ROOT = Path(tempfile.mkdtemp())  # no specs/figma.json here

    def tearDown(self):
        ingest.ROOT = self.root

    def test_html_is_measurable(self):
        self.assertEqual(ingest.check_design(self.rows("home.html", "home.png")), "")

    def test_images_only_is_a_gap(self):
        gap = ingest.check_design(self.rows("home.png", "flow.pdf"))
        self.assertIn("PROTOTYPE GAP", gap)
        self.assertIn(".pdf, .png", gap)

    def test_figma_config_closes_the_gap(self):
        (ingest.ROOT / "specs").mkdir()
        (ingest.ROOT / "specs" / "figma.json").write_text("{}", encoding="utf-8")
        self.assertEqual(ingest.check_design(self.rows("home.png")), "")


if __name__ == "__main__":
    unittest.main()
