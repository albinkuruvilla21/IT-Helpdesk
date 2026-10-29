---
name: verify
description: Runs every automated check on the Power Apps project (solution build and validation, control properties, token discipline, list schemas, AC traceability, flows, connectors, secrets, version) and reports. With "release", also bumps the version, builds the managed and unmanaged solution ZIPs and writes the release notes (stage G11). Use when the user runs /verify, before marking any stage Done, or before a deployment.
argument-hint: "[release]"
---

# /verify: health check, and stage G11 with `release`

Run every check below, even after an early failure, and report them together as a table:
check · result · detail. Fix nothing silently; if the user asks you to fix something, fix it and run
the whole set again.

Keep **static** results and **Studio / run-time** results apart (`docs/standards/powerfx-validation.md` §1): checks 1–15 and 17–20
are static; 16 is Studio. A clean static run is reported as *"static checks pass; not yet opened in Studio"* until check 16 is
confirmed, never as "the app works" or "the formulas are error-free".

## Checks

| # | Check | How | Pass |
|---|---|---|---|
| 1 | Solution builds and validates | `uv run tools/pp.py build` | 0 errors. Report every warning |
| 2 | Control properties | Part of 1: "N control(s) checked"; any `not checked` warning names controls Studio must confirm | No `unknown property`; unchecked controls listed |
| 3 | No literals on screens (D11) | Command A below | No output |
| 4 | List schemas | `uv run tools/check_schemas.py` | 0 errors |
| 5 | AC workbook and traceability | `uv run tools/ac_workbook.py check specs/acceptance-criteria/<CODE>_AcceptanceCriteria.xlsx --src canvas --src solution/src` | 0 errors; list the warnings |
| 6 | YAML ↔ schema | Part of 1 and 18: `FX-SCHEMA` (every list a formula names, every column read or written, is in its CSV), `FX-INDEX` (every column a `Filter`/`LookUp`/`Sort`/`SortByColumns` on a list uses is `Indexed="TRUE"`), `FX-PATCH`. Report the "names in record scope … not checked" count: those depend on Studio | No error |
| 7 | Flows | Part of 1 (references, variables, connectors, HTTP, values); plus every `$filter` field indexed in its CSV | Clean |
| 8 | Connectors (D2) | `pp.config.json` → `allowedConnectors` holds only standard connectors; any addition since the template is recorded in PROJECT.md §3 | Clean |
| 9 | Secrets and real data | Part of 1 (emails, tenant hosts, SAS, secrets in flows, variables and YAML), plus command B over the repository | Nothing |
| 10 | Mocks and stubs | Command C; at release also check 18 with `--release` (it fails `TODO(AC-…)` and `Mock…` in formulas) | Nothing, at release |
| 11 | Samples gone | Command D | Nothing, after G6 |
| 12 | Settings files (only if the project uses `deployment/settings.<env>.json` for scripted imports; otherwise skip) | `uv run tools/pp.py settings` | Every variable and reference present in each file |
| 13 | Version | `<Version>` in `solution/src/Other/Solution.xml` is above the last release in PROJECT.md §7 | Higher |
| 14 | Stages | PROJECT.md §2 | Report each stage's status; flag any `Reopened`, and G2 if not `Approved` |
| 15 | UI library | `uv run tools/canvas_ui.py --selftest` | Identical to `samples/powerapp` |
| 16 | Opened in Studio (level 3) | Ask whether the current version has been opened in Studio from the imported solution, with lists bound and flows added, and what **App checker → Formulas** and **Rules** show, and whether any delegation warning remains | 0 formula errors, no delegation warning, Saved and Published; who and when. State plainly "not yet opened in Studio" if not: a clean build proves neither the layout (PA-T22) nor the formulas (powerfx-validation §6) |
| 17 | Prototype fidelity (CLAUDE.md §7) | `specs/prototype-fidelity.md` exists (after G1); command E; every `Deviation` row has a design-spec §9 row with a reason prototype-fidelity §6 allows; every view in its §1 is a screen or dialog in build-plan §1 or an `Out of Scope` row | After G7: no `Not built` row. Report the counts by status, and the `Built` rows as "not yet compared in Studio" |
| 18 | Formulas, static (levels 1–2) | `uv run tools/pp.py fx` (`--release` with `release`); the same checks run inside 1 | 0 errors. The formula line says *syntax confirmed by Microsoft's Power Fx parser* (else flag it: the stdlib fallback is not the authority). Report warnings grouped by code (`FX-DELEG`, `FX-ERRHANDLING`, `FX-PATCH`, `FX-TEXT`, `FX-AC`, …) and every `fx-ignore` with its reason |
| 19 | The checks themselves | `uv run python -m unittest discover -s tools/tests`, then `uv run tools/powerfx.py --selftest`, `uv run tools/prototype_design.py --selftest` | All pass (a skipped Microsoft-parser test is reported as skipped, not passed); the Studio-built sample has no Studio-class finding |
| 20 | Prototype look (CLAUDE.md §7 rule 5) | If `inputs/design/` holds an HTML prototype: `uv run tools/prototype_design.py inputs/design/<file>.html --content <w> --check canvas/<App>/Src/App.pa.yaml` | 0 errors (every measured colour is a token; `IsDark` when the prototype has a dark scheme). Each warning is a compliant variant listed in design-spec §8 |
| 21 | Prototype ↔ Studio (optional) | If `specs/visual-map.json` exists and Studio screenshots are in `specs/screenshots/`: `uv run tools/visual_compare.py run`, then look at each comparison image. Otherwise skip it and say so | **Reports only, never blocks.** List each entry `matches`, `accepted` or `differs`; a `differs` entry is a difference to fix or record in design-spec §9. Entries with no screenshot are "not yet compared in Studio", like a `Built` register row |

```bash
# A — colour literals on screens (tokens live in App.Formulas only)
grep -nE 'RGBA\(|ColorValue\(|#[0-9A-Fa-f]{6}\b' canvas/*/Src/scr*.pa.yaml
# B — secrets
grep -rnIiE 'client_secret|password=|AccountKey=|[?&]sig=|Bearer [A-Za-z0-9]' . --exclude-dir={inputs,.git,dist}
# C — mock data and stubs left by /scaffold
grep -rnE 'Mock[A-Z]|MockState|TODO\(AC' canvas/*/Src
# D — starter samples
grep -rnE 'SampleList|SampleNotify|Say hello' canvas solution/src deployment
# E — prototype register rows not built, or built but not yet compared in Studio
grep -nE '^\| P-[0-9]+ ' specs/prototype-fidelity.md | grep -E '\| (Not built|Built) \|'
```

## `release`

Only if checks 1–13, 18 (with `--release`), 19 and 20 pass (21 is reported, never required), G2 is `Approved`, and G8, G9 and G10 are `Done`:

1. `uv run tools/pp.py bump` (build number; `--part minor` for a release with new features), above the
   last release in PROJECT.md §7 and `specs/release-notes.md` (PA-T11).
2. `uv run tools/pp.py build`. Report both ZIPs (`dist/<Solution>_<v>.zip` and `_managed.zip`) with sizes.
3. List what the importer must choose in the portal's import wizard (environment variables from PROJECT.md
   §6.2, connection references from §6.3), for the release notes. Values never go in the solution.
4. Write `specs/release-notes.md` from `docs/templates/release-notes.template.md`: test results from the
   workbook's latest iteration (`dump --format json`, counted by status), known issues (failing or blocked
   tests, `pp.py` warnings, every `fx-ignore` suppression with its reason, 🔶 items), every deviation from the prototype (register §3,
   with its reason), **formula validation by level** (static: the parser and version, 0 errors; Studio App checker: result, who, when,
   or "not yet opened in Studio"; acceptance checks walked: which), and the deployment steps for this release.
5. Copy both ZIPs to `releases/` at the repository root, under the same names
   (`releases/<Solution>_<v>_managed.zip` and `releases/<Solution>_<v>.zip`). `dist/` is build output and stays ignored;
   `releases/` is what people import (`releases/README.md`). Never overwrite a file already there: a fix is a new version.
6. PROJECT.md G11 → `Done`. Commit the ZIPs, the release notes, the version bump and PROJECT.md:
   `G11: release <version>`. The **delivery lead** reviews the release candidate and imports it from `releases/`. You
   never import into Test or Prod, and never run `pp.py check` or `import` unasked.
