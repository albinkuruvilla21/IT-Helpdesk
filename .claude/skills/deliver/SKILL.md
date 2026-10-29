---
name: deliver
description: Runs every stage after the acceptance criteria sign-off (G3–G11) end to end in one go (design spec, build plan, list schemas, scaffold, UI, functionality, flows, test cases, release candidate solution ZIP) without stopping for per-stage approvals, and ends with a list of what people still have to do. Resumes from the first stage not Done. Use when the user runs /deliver or asks to build the whole Power Apps project after the AC is signed off.
argument-hint: "[optional: 'from G<n>' to start at a stage]"
disable-model-invocation: true
---

# /deliver: G3–G11 in one run

The Client PO has signed off the acceptance criteria. From here to a release candidate there are no
approvals: run each stage, mark it `Done`, commit, and carry on. People review the release candidate
as a whole.

## 0. Before you start

- `PROJECT.md` §2: **G2 must be `Approved`**, with the PO's name and date. Otherwise stop: "The
  acceptance criteria need the Client PO's sign-off (PROJECT.md G2) before `/deliver` runs."
- `uv run tools/ac_workbook.py check <workbook>` must report **0 errors** and at least one `Approved` row.
  A workbook with statuses outside the format, missing sheets or no live rows can't be built from: stop
  and say what the check found.
- `uv run tools/pp.py doctor` passes.
- Start at the first stage in §1 that isn't `Done` (a `Reopened` stage isn't), or where `$ARGUMENTS`
  says. Skip stages already `Done`.
- Start an **outstanding list**: things only a person can do. It grows through the run and ends the
  report.

## 1. The run

Run each stage by following its own SKILL.md **in full** (reads, rules, checks), except where this
file overrides it. Open the SKILL.md each time; don't run a stage from memory.

| Stage | Skill | In this run |
|---|---|---|
| G3 | `/design-spec` | |
| G4 | `/build-plan` | |
| G5 | `/list-schemas` | Outstanding: import the lists on the dev site (README **Creating the lists**) |
| G6 | `/scaffold` | |
| G7 | `/ui-dev` | All screens, each compared with the prototype in source (register rows `Built`). Outstanding: import the unmanaged ZIP into Dev, open the app in Studio, Save, Publish (PA-T8), optionally, screenshot each screen's canvas for every entry in `specs/visual-map.json` into `specs/screenshots/`, then `uv run tools/visual_compare.py run` and look at each comparison (rows → `Matched`) |
| G8 | `/functionality-dev` | All screens. Don't ask about the lists. Outstanding: in Dev, add each list as a data source from inside the solution (PA-T13) and each flow (PA-T26), App checker → Formulas 0 errors and no delegation warning (powerfx-validation level 3), `pp.py export`, then walk each screen's checks (level 4) |
| G9 | `/flows` | If build-plan §5 lists none, mark G9 `Done` with the note "no flows". Outstanding: bind the connection references, set the variables, turn each flow on, run it once |
| G10 | `/test-cases` | Outstanding: execute the tests and record results in the workbook |
| G11 | `/verify release` | |

After each stage:

1. Its checks pass.
2. PROJECT.md §2: the stage → `Done`. New questions → §4.
3. Commit: `G<n>: <stage>` (e.g. `G4: build plan`).
4. One line to the user (stage done, what it produced), then straight on to the next. Don't wait for
   a reply.

## 2. What doesn't stop the run

| Situation | Do |
|---|---|
| An AC check is ambiguous | Narrowest reading; `// AC-… assumes <x>, see Q-nn`; the question in PROJECT.md §4 |
| A design value or state the inputs don't settle | Propose it ("not in design: proposed"), 🔶, question in §4 |
| A tenant fact is 🔶 | The Acies default (CLAUDE.md §4) applies; note it |
| A control the design needs is outside dev-standards §2 | Use the closest checked control, record the deviation (design-spec §9), and put the spike in build-plan §7 |
| The prototype shows something the library has no pattern for, or that is harder to build | Build it as the prototype shows (prototype-fidelity §5), extending the library where needed (ui-patterns §9). Never simplify, redesign or leave it out to keep the run moving; a true platform limitation is a recorded deviation |
| The prototype shows a whole feature with no AC row and no `Out of Scope` row | Don't build it and don't drop it silently: a proposed change (`/acceptance-criteria` §6), the register's §4, and the report |
| A later stage needs an earlier artefact changed (e.g. a column G8 needs) | Change it under that stage's rules (schemas: append only, never alter an existing field), re-run that stage's checks, and note it in the report |
| A step that needs a person or Studio | Add it to the outstanding list and carry on |

## 3. What stops it

Stop, leave the current stage `In progress`, commit what is done, and report what's needed. Running
`/deliver` again resumes there.

- A need to break an Acies default (CLAUDE.md §4) that PROJECT.md §3/§5 doesn't record, with no
  compliant alternative (a premium connector, Azure, a secret). If there is a compliant alternative,
  use it and say so.
- A check that still fails after a real attempt to fix the cause (never by weakening the check, and
  never by editing `allowedConnectors` or `tools/canvas-control-templates.json` to make it pass).
- An input the stage can't do without (e.g. no design files for `/design-spec`).
- Anything that would run against a client environment or tenant (`pp.py import`, `export`, `check`).
  The deliverable is the ZIP; people import it through the portal and choose the variable values there.
  You never do that inside `/deliver`.

## 4. Finish

When G11 is `Done`, give back to the reuse catalogue: `/catalogue contribute` steps 1–3
(`.claude/skills/catalogue/SKILL.md` §3). Draft the entries and usage rows in `specs/catalogue/` and
commit them (`G11: catalogue entries`); don't open the pull request yet. If the catalogue can't be
reached, say so and carry on.

Then reply with:

1. A stage table: stage · status · commit.
2. What was built: screens (with their AC IDs), lists, environment variables, connection references,
   flows, the number of test cases, and the ZIP paths, version and sizes.
3. Prototype fidelity: the register's counts by status, and every deviation with its reason.
   Formula validation by level (`docs/standards/powerfx-validation.md` §1): static (parser and version, 0 errors, warnings and
   suppressions); Studio and run time as outstanding until a person has done them.
4. Assumptions and questions raised during the run (`Q-nn`), and anything changed upstream mid-run.
5. **Outstanding before anyone deploys:** the list, in order, each with who does it.
6. **Catalogue:** the entries drafted, the usage rows added, the pieces skipped as client-specific,
   and a question: open the catalogue pull request now? (`/catalogue contribute` §3 step 4)

End with: "This is a release candidate, not a deployment. The delivery lead reviews it and imports it;
I don't."
