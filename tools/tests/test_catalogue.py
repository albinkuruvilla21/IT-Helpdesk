"""Tests for tools/catalogue.py: the search ranks by keywords, skips Deprecated entries, and prints both formats."""
import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import catalogue  # noqa: E402

POOL = [
    {"id": "request-approval-flow", "name": "Request approval with email", "type": "Cloud flow", "summary": "Emails an approver.",
     "capabilities": ["Email"], "keywords": ["approval", "email"], "status": "Usable", "reuse": {"rights": "Acies-owned"}},
    {"id": "approval-screen", "name": "Approvals screen", "type": "Canvas screen", "summary": "Approve or reject.",
     "capabilities": ["Approve", "Reject"], "keywords": ["approval", "gallery"], "status": "Usable", "reuse": {"rights": "Acies-owned"},
     "toolchain": {"pac": "2.13", "studio": "3.26091"}},
    {"id": "old-approval", "name": "Old approval", "type": "Cloud flow", "summary": "approval", "capabilities": [],
     "keywords": ["approval"], "status": "Deprecated", "reuse": {"rights": "Acies-owned"}},
]


class CatalogueTests(unittest.TestCase):
    def test_search_finds_and_skips_deprecated(self):
        ids = [e["id"] for e in catalogue.search(["approval"], 10, POOL)]
        self.assertIn("request-approval-flow", ids)
        self.assertIn("approval-screen", ids)
        self.assertNotIn("old-approval", ids)

    def test_search_ranks_the_better_match_first(self):
        ids = [e["id"] for e in catalogue.search(["gallery", "approval"], 10, POOL)]
        self.assertEqual(ids[0], "approval-screen")

    def test_search_miss_is_empty_not_an_error(self):
        self.assertEqual(catalogue.search(["carousel"], 10, POOL), [])

    def test_short_words_are_ignored(self):
        self.assertEqual(catalogue.search(["of", "an"], 10, POOL), [])

    def test_toolchain_column(self):
        self.assertEqual(catalogue._chain(POOL[1]), "2.13 / 3.26091")
        self.assertEqual(catalogue._chain(POOL[0]), "—")

    def test_show_prints_a_table_or_a_message(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            catalogue.show(POOL[:1], "md")
            catalogue.show([], "md")
        self.assertIn("`request-approval-flow`", out.getvalue())
        self.assertIn("No entries.", out.getvalue())

    def test_config_points_at_the_powerapps_catalogue(self):
        self.assertTrue(catalogue.config()["repository"].endswith("acies-powerapps-catalogue"))


if __name__ == "__main__":
    unittest.main()
