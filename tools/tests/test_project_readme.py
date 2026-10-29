"""Tests for pp.py setup's README swap: the template's introduction and getting-started blocks become the project's own,
and the how-to sections stay.

    uv run python -m unittest discover -s tools/tests -v
"""
import argparse
import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import pp  # noqa: E402


class ProjectReadmeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "docs" / "templates").mkdir(parents=True)
        shutil.copy(ROOT / "README.md", self.tmp / "README.md")
        shutil.copy(ROOT / "docs" / "templates" / "project-readme.template.md", self.tmp / "docs" / "templates")
        self.old, pp.ROOT = pp.ROOT, self.tmp

    def tearDown(self):
        pp.ROOT = self.old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def setup_readme(self):
        args = argparse.Namespace(client="Contoso", project="Site Requests")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            pp.fill_readme(args, "CON", "ContosoSiteRequests", "con", "Site Requests")
        return (self.tmp / "README.md").read_text(encoding="utf-8"), out.getvalue()

    def test_template_readme_has_both_blocks(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for block in ("intro", "start"):
            self.assertIn(f"<!-- README:{block} -->", text)
            self.assertIn(f"<!-- /README:{block} -->", text)

    def test_blocks_become_the_projects(self):
        text, out = self.setup_readme()
        self.assertEqual(out, "")
        self.assertIn("# Contoso — Site Requests", text)
        self.assertIn("## Joining this project", text)
        self.assertIn("`ContosoSiteRequests`", text)
        self.assertIn("`con_`", text)
        self.assertNotIn("# Acies Power Apps delivery template", text)
        self.assertNotIn("## Starting a project", text)
        self.assertNotIn("{Client}", text)

    def test_how_to_sections_stay(self):
        text, _ = self.setup_readme()
        for heading in ("## Prerequisites", "## Setting up the Python tools", "## Importing", "## The reuse catalogue"):
            self.assertIn(heading, text)

    def test_line_endings_are_kept(self):
        readme = self.tmp / "README.md"
        readme.write_bytes(readme.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        self.setup_readme()
        data = readme.read_bytes()
        self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))

    def test_missing_markers_leave_the_readme_alone(self):
        readme = self.tmp / "README.md"
        readme.write_text("# Someone's own README\n", encoding="utf-8")
        text, out = self.setup_readme()
        self.assertEqual(text, "# Someone's own README\n")
        self.assertIn("no <!-- README:intro --> block", out)


if __name__ == "__main__":
    unittest.main()
