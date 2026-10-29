"""Tests for tools/ac_workbook.py check: AC IDs are AC-<PROJECT>-NN, and the code must be the workbook's project code.

    uv run python -m unittest discover -s tools/tests -v
"""
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

try:
    import openpyxl  # noqa: F401
    import ac_workbook  # noqa: E402
except ImportError:  # run through uv run, which installs openpyxl
    ac_workbook = None

SAMPLE = ROOT / "samples" / "acceptance-criteria" / "Sample_AcceptanceCriteria.json"


def build_and_check(data: dict, src=None) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        xl = Path(tmp) / "ac.xlsx"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ac_workbook.build(data, xl, True)
            code = ac_workbook.check(xl, src)
        return code, out.getvalue()


@unittest.skipIf(ac_workbook is None, "openpyxl not installed: run through uv run")
class AcIdTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(SAMPLE.read_text(encoding="utf-8"))

    def test_sample_uses_the_project_code(self):
        code = self.data["project"]["code"]
        for a in self.data["acceptanceCriteria"]:
            self.assertTrue(a["id"].startswith(f"AC-{code}-"), a["id"])

    def test_sample_passes(self):
        code, out = build_and_check(self.data, [ROOT / "canvas", ROOT / "solution" / "src"])
        self.assertEqual(code, 0, out)
        self.assertNotIn("must use the project code", out)

    def test_wrong_project_code_fails(self):
        bad = copy.deepcopy(self.data)
        old = bad["acceptanceCriteria"][0]["id"]
        bad["acceptanceCriteria"][0]["id"] = old.replace(f"AC-{bad['project']['code']}-", "AC-HOME-")
        code, out = build_and_check(bad)
        self.assertNotEqual(code, 0)
        self.assertIn("must use the project code", out)

    def test_area_style_id_is_rejected_when_the_code_differs(self):
        bad = copy.deepcopy(self.data)
        bad["acceptanceCriteria"][0]["id"] = "AC-REQ-01"
        code, out = build_and_check(bad)
        self.assertNotEqual(code, 0)
        self.assertIn("AC-REQ-01", out)


if __name__ == "__main__":
    unittest.main()
