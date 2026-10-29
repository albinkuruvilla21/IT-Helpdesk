"""Tests for tools/visual_compare.py: the prototype measured in Chromium (view, scheme, clock, inherited type, scale) and the
comparison with a Studio screenshot (match, difference, accepted, missing, wrong shape).

    uv run python -m unittest discover -s tools/tests -v
The browser tests skip when Playwright or Chromium is missing (uv run playwright install chromium).
"""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import visual_compare as vc  # noqa: E402

SAMPLE_MAP = ROOT / "samples" / "design" / "SAMPLE-visual-map.json"

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None


def chromium_ok() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


CHROMIUM = chromium_ok()


@unittest.skipIf(Image is None, "Pillow not installed: run through uv run")
class CompareImageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def image(self, name, size=(400, 200), box=None, colour=(30, 90, 200)):
        im = Image.new("RGB", size, "white")
        ImageDraw.Draw(im).rectangle([20, 20, 380, 60], fill=(15, 108, 189))
        if box:
            ImageDraw.Draw(im).rectangle(box, fill=colour)
        p = self.tmp / name
        im.save(p)
        return p

    def test_identical_is_zero(self):
        r = vc.compare_images(self.image("a.png"), self.image("b.png"), self.tmp / "s.png")
        self.assertEqual(r["share"], 0)
        self.assertTrue((self.tmp / "s.png").exists())

    def test_a_missing_block_is_counted(self):
        r = vc.compare_images(self.image("a.png"), self.image("b.png", box=[0, 100, 400, 200], colour=(0, 0, 0)), self.tmp / "s.png")
        self.assertGreater(r["share"], 0.4)

    def test_a_bigger_screenshot_of_the_same_shape_is_resized(self):
        big = Image.open(self.image("a.png")).resize((800, 400))
        big.save(self.tmp / "big.png")
        r = vc.compare_images(self.image("a.png"), self.tmp / "big.png", self.tmp / "s.png")
        self.assertLess(r["share"], 0.02)
        self.assertEqual(r["aspect"], 0)
        self.assertEqual(r["screenshot"], "800 x 400")

    def test_verdicts(self):
        self.assertEqual(vc.verdict({}, None, 0.08), "no screenshot")
        self.assertEqual(vc.verdict({}, {"share": 0.05, "aspect": 0}, 0.08), "matches")
        self.assertEqual(vc.verdict({}, {"share": 0.2, "aspect": 0}, 0.08), "differs")
        self.assertEqual(vc.verdict({"accepted": "DEV-01"}, {"share": 0.2, "aspect": 0}, 0.08), "accepted")
        self.assertEqual(vc.verdict({}, {"share": 0.0, "aspect": 0.2}, 0.08), "differs")  # a different shape is a layout difference

    def test_units(self):
        self.assertEqual(vc.scaled("16px 8px", 0.5), "8 4")
        self.assertEqual(vc.scaled("rgba(0, 0, 0, 0.08) 0px 4px 12px 0px", 0.5), "rgba(0, 0, 0, 0.08) 0 2 6 0")
        self.assertEqual(vc.hexcolour("rgb(15, 108, 189)"), "#0F6CBD")
        self.assertEqual(vc.hexcolour("rgba(0, 0, 0, 0.5)"), "#000000 @0.5")


@unittest.skipUnless(CHROMIUM and Image is not None, "Playwright's Chromium not installed: uv run playwright install chromium")
class PrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = vc.load_map(SAMPLE_MAP)
        cls.tmp = Path(tempfile.mkdtemp())
        cls.out, vc.OUT = vc.OUT, cls.tmp / "out"
        with vc.Browser() as b:
            cls.home = vc.measure_entry(b, cls.cfg, vc.pick(cls.cfg, "scrHome", "ready", "light"))
            cls.dark = vc.measure_entry(b, cls.cfg, vc.pick(cls.cfg, "scrHome", "ready", "dark"))
            cls.reqs = vc.measure_entry(b, cls.cfg, vc.pick(cls.cfg, "scrMyRequests", "empty", "light"))

    @classmethod
    def tearDownClass(cls):
        vc.OUT = cls.out
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def texts(self, found):
        return [t["text"] for t in found["texts"]]

    def test_the_clock_is_frozen(self):
        self.assertIn("Wednesday, 28 October 2026", self.texts(self.home))

    def test_a_script_drawn_view_is_measured(self):
        self.assertIn("You haven't asked for a site yet.", self.texts(self.reqs))
        self.assertNotIn("Welcome", self.texts(self.reqs))
        self.assertIn("Welcome", self.texts(self.home))

    def test_the_dark_scheme_is_rendered(self):
        header = lambda f: next(b for b in f["boxes"] if b["tag"] == "header")["backgroundColor"]
        self.assertEqual(vc.hexcolour(header(self.home)), "#FFFFFF")
        self.assertEqual(vc.hexcolour(header(self.dark)), "#1C232D")

    def test_inherited_type_and_scale(self):
        values = vc.to_app(self.home, 0.5)
        body = next(t for t in values["texts"] if t["text"].startswith("Ask for a new"))
        self.assertEqual(body["px"], 14)            # inherited from body: static CSS reading can't see this on the <p>
        self.assertEqual(body["pt"], 5.2)           # 14 x 0.5 x 0.75 = 5.25
        header = next(b for b in values["boxes"] if b["box"] == "header")
        self.assertEqual(header["radius"], "8")
        self.assertEqual(header["padding"], "8 12 8 12")

    def run_map(self, screens, strict=False):
        m = dict(json.loads(SAMPLE_MAP.read_text(encoding="utf-8")), screens=screens)
        path = self.tmp / "map.json"
        path.write_text(json.dumps(m), encoding="utf-8")
        args = ["--map", str(path), "run"] + (["--strict"] if strict else [])
        with contextlib.redirect_stdout(io.StringIO()):
            code = vc.main(args)
        return code, json.loads((vc.OUT / "report.json").read_text(encoding="utf-8"))

    def test_run_matches_differs_accepts_and_requires_screenshots(self):
        base = {"screen": "scrHome", "design": "samples/design/SAMPLE-prototype.html", "region": "#app"}
        # The prototype's own render stands in for a perfect Studio screenshot.
        code, _ = self.run_map([dict(base, state="ready", scheme="light")])
        good = self.tmp / "good.png"
        shutil.copy(vc.OUT / "scrHome-ready-light.prototype.png", good)
        bad = self.tmp / "bad.png"
        im = Image.open(good)
        ImageDraw.Draw(im).rectangle([0, 300, im.width, im.height], fill=(0, 0, 0))
        im.save(bad)
        code, report = self.run_map([
            dict(base, state="ready", scheme="light", screenshot=str(good)),
            dict(base, state="wrong", scheme="light", screenshot=str(bad)),
            dict(base, state="agreed", scheme="light", screenshot=str(bad), accepted="design-spec §9 DEV-09: test"),
        ], strict=True)
        self.assertEqual([r["verdict"] for r in report], ["matches", "differs", "accepted"])
        self.assertEqual(report[0]["share"], 0)
        self.assertEqual(code, 1)  # --strict fails on the difference
        code, report = self.run_map([dict(base, state="ready", scheme="light", screenshot=str(good)),
                                     dict(base, state="none", scheme="light")], strict=True)
        self.assertEqual(report[1]["verdict"], "no screenshot")
        self.assertEqual(code, 1)  # --strict fails on a missing screenshot too
        code, _ = self.run_map([dict(base, state="ready", scheme="light", screenshot=str(good))], strict=True)
        self.assertEqual(code, 0)

    def test_a_missing_region_is_reported(self):
        e = dict(vc.pick(self.cfg, "scrHome", "ready", "light"), region="#nowhere")
        with vc.Browser() as b, self.assertRaises(SystemExit) as ctx:
            vc.measure_entry(b, self.cfg, e)
        self.assertIn("#nowhere", str(ctx.exception.code))


if __name__ == "__main__":
    unittest.main()
