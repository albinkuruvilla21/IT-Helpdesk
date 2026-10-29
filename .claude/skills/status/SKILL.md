---
name: status
description: Reports where the Power Apps project stands (every stage, what is blocking, what to do next) and detects changes since stages were done, such as an input file changed after ingest, an acceptance criterion altered after sign-off, or source out of step with the last build, listing what they affect. Use when the user runs /status, asks "where are we", "what's next", or asks what a change affects.
---

# /status: where the project stands

Read-only unless the user agrees to the changes you propose.

## 1. Gather

- `PROJECT.md`: §2 stages and the G2 sign-off, §4 open questions without answers, §5 🔶 tenant facts,
  §6 environments and settings, §7 the last release.
- `uv run tools/ingest.py --status`: inputs new or changed since the last ingest.
- `git status --porcelain inputs/`: input files not yet committed. Other developers can't see them; say so,
  unless PROJECT.md §3 records that inputs stay off GitHub.
- If the AC workbook exists, `uv run tools/ac_workbook.py dump <workbook> --format json`: rows with status
  `Changed` (and their dated Alterations), `In Review`/`Draft`/`Candidate` rows, `Open` questions on the
  Questions sheet, `Awaiting` client inputs, and test results by status.
- If the project uses settings files: `uv run tools/pp.py settings`: which are incomplete.
- The solution version in `solution/src/Other/Solution.xml` against the last release in PROJECT.md §7
  (a release needs a higher one).
- `git log --oneline -15` for recent stage commits; `git status` for uncommitted source.

## 2. Detect what an upstream change affects

| Change | Affected |
|---|---|
| An input file changed after G1 | G1, and every `Done` stage built from it: BRD/transcript → G2 onward (the signed-off workbook needs a change proposal, `/acceptance-criteria` §6); design/branding → G3 onward |
| An AC row `Changed` after the G2 sign-off | The screens and flows (build-plan §1, §5) and lists (§2) naming that AC ID; its test cases (re-run); G4–G9 and G10 where they are affected |
| A schema CSV changed after G5 | The formulas using that list (G8); the dev and production lists need re-importing; the app's data source needs refreshing in Studio |
| Tokens (`App.Formulas`) changed after G7 | Visual re-check of every screen (G7) |
| The prototype changed after G1 | The register (`/ingest` re-inventories the changed views), the AC (a change proposal once signed off), and G3 onward for the screens those views become |
| Register rows `Not built` after G7, or `Built` but not compared in Studio | The screens they belong to (G7, G8); the comparison goes on the outstanding list |
| The app or a flow changed in the Dev environment | Source is behind: `uv run tools/pp.py export`, review the diff, commit |
| Version not above the last release | The next import into Test or Prod will be refused or skipped: `pp.py bump` (PA-T11) |

**Propose** setting each affected stage to `Reopened`, with the reason. Change PROJECT.md only once the
user agrees. `/deliver` then re-runs the reopened stages for the affected scope.

## 3. Report

1. A stage table: stage · status · note, plus who signed off G2 and when.
2. **Next action**: the one skill to run next (after sign-off, usually `/deliver`), or the PO's
   sign-off if that is what's awaited.
3. Blockers: unanswered questions (with owner), awaited client inputs, 🔶 tenant facts that block
   something specific (no Dev environment, no service account, DLP unknown).
4. Changes since stages were done, and what they affect (from §2).

Keep it to one screen.
