# Lessons learned from the first project

The first project built with this template (a request-and-approval app with email flows, 22 acceptance criteria, six screens, six flows) found every
problem listed here. Each one is now **guarded**: by a check in `pp.py build`, a rule in a standard, a library, or a skill. Read this once; the guards do
the rest. Add a row when a project finds something new, and add its guard the same session (a check in `tools/pp.py` is worth ten notes).

## 1. What failed, and what now stops it

| # | What happened | Root cause | Guard |
|---|---|---|---|
| 1 | Studio refused the app: `PA2108 Unknown property 'LayoutMode' ... 'AutoLayout'` and `'Layout' ... 'Gallery' ... 'Vertical'` | The control's template lists the property, but the variant does not take it. `pac canvas pack` checks nothing | `pp.py build` fails it (PA-T21). `canvas_ui` never emits it |
| 2 | Screens built and imported but **laid out badly** (clipped text, inputs past their section, cut-off buttons). Rebuilt three times | Layout generated from tokens, computed sizes, nested flexible auto-layout, container badges | **The rule: never invent a layout** (`ui-patterns.md`, PA-T22, CLAUDE.md D11). Clone a Studio-built reference app or use `tools/canvas_ui.py`; its `--selftest` proves it matches the reference. `/scaffold`, `/ui-dev` enforce it |
| 3 | `PA2110 An entity with name 'docHdr' already exists` | A screen prefix plus a part name collided (`doc` + `Hdr`) | `pp.py build` fails duplicate names per screen (PA-T23); `canvas_ui` asserts |
| 4 | `PA1001 YamlInvalidSyntax ... did not find expected key` | A traceability comment appended **after** the closing quote of a quoted formula | `pp.py build` lints it (and parses fully if PyYAML is installed) (PA-T25) |
| 5 | `PA2105 ... older than the current version` (ModernDropdown 1.0.2 vs 1.0.3) | The checker's template list was older than the user's Studio | `tools/canvas-control-templates.json` refreshed from a Studio-saved app; do it again when Studio moves (dev-standards §12) |
| 6 | A button did nothing and said nothing, with a red mark on its formula | The formula called `'Flow'.Run(...)`; the app was opened as a loose `.msapp`, so the flows could not be added to it | `pp.py build` names every flow the app calls in a warning (PA-T26). Open the app **from the imported solution**, then add the flows |
| 7 | The same silent button, after a column and a list were added to `schemas/` | The site's lists and Studio's cached schema were older than the repository | `pp.py build` fails a list or written column that is not in `schemas/` (PA-T27). After any schema change: re-run the importer, **Refresh** the data source in Studio, add new lists |
| 8 | Header name blank, coverage list empty, a button's text blank | `OnStart` had not run in the authoring session | Documented (`ui-patterns.md` section 7): **Run OnStart** once after opening |
| 9 | `pp.py build` reported one error about a ZIP "being used by another process", then 0 on the next run | A scanner or indexer held the freshly written file | Retry after a few seconds (PA-T24); never "fix" the solution |
| 10 | A form with 5 rows left a large empty block; a "Select" header wrapped | The reference was sized for 13 rows and a column too narrow | Heights that depend on a list are `CountRows(...) * row` (ui-patterns); library defaults are the proven widths |
| 11 | The checker passed and the user still saw problems | `pp.py build` checks names, not layout, formulas or data | Say **"not yet opened in Studio"** until someone has opened the app and the errors it showed are fixed. `/verify` check 16 |
| 12 | A check I wrote looked right and checked nothing (wrong offset) | A check that has never failed is unproven | **Prove every new check by breaking something on purpose** and watching it fail, then restore |
| 13 | The template's own starter screen showed `User().FullName` as words, and a quote mark in the header band, and every build passed | Formulas were never parsed: `pac canvas pack` doesn't, and `pp.py` checked only names around them. `canvas_ui.chrome()` quoted a formula | Every formula is parsed by Microsoft's Power Fx parser and checked statically (`pp.py fx`, `build`; [powerfx-validation.md](standards/powerfx-validation.md)); PA-T28, PA-T29. Still "not yet opened in Studio" until it is (row 11) |
| 14 | The first Studio open showed formula errors the static checks had passed: `Navigate` in `OnVisible`, an `IfError` mixing a table and a boolean, list names that Studio had renamed, and Approve and Reject pushed out of a fixed-height row | The checks knew the syntax and the names, not three of Studio's rules; a row height was a guess | PA-T30, T31, T32 with checks (`FX-NAV`, `FX-TYPE`, the display-name check); a row that holds a table and buttons takes its height from the table (ui-patterns §7); each new Studio error is a check and a trap the same session (row 12) |
| 15 | The second Studio open still showed 29 formula errors: `ShowColumns` with text, `ErrorKind.EditPermission`, a dropdown `Default` that was text | I wrote formulas from memory of Power Fx instead of from what Studio accepts, and one bad `OnStart` formula made most of the others fail | PA-T33 to T35 with checks (`FX-ARG`, `FX-ENUM`, `FX-TYPE`); use only constructs the Studio-built sample or Microsoft's docs show; read App's errors first |
| 16 | With the formulas clean, the screens were still wrong: the header title wrapped, and the entry card and weekly table were cut off | A library note said a section may size itself; Studio does not do that for formula heights or galleries; a title label had no slack | PA-T36, T37; sections always get an explicit, formula-driven `Height`; look at each screen with no rows, one row and many rows before calling it done |
| 17 | The second project's app opened cleanly and looked nothing like the accepted prototype: a flat header instead of a floating bar with pill tabs, small type, square opaque cards, a bar instead of a ring, light only | The template told screens to use the reference app's numbers and chrome ("sizes are the plain numbers"), colours were chosen by hand, and deviations like "corners and shadows aren't native" were accepted without checking the control templates (they are) | Prototype measured by `tools/prototype_design.py` (both schemes, type scale, geometry); `canvas_ui` patterns for the look (`floating_topbar`, `panel`, glass `box`, `svg_backdrop`, `svg_ring`, `svg_tile`, pill buttons, `IsDark` tokens); prototype-fidelity §8, ui-patterns §10; `/verify` check 20 fails a measured colour with no token. Check the templates before calling anything not native |
| 18 | The third project's first Studio pass: the form's dropdowns showed on every screen; the ticket table's pill columns vanished and its headings ran off the card; the pager buttons showed "ious pag"; the status bars had no fill; a tile title and an empty-state line were cut off; and `{Name: Name}` on an Attachments table was an error | Everything passed `pp.py build`. Helpers had no `Visible` parameter; sizes were chosen for the shortest sample row; `Text(x, "0.##")` was trusted in an SVG; a Classic button holds text it cannot hide; the Attachments columns were guessed | PA-T40 to PA-T48; `FX-OVERLAY`, `FX-SVG`, `FX-NAME` (Attachments) in `tools/powerfx.py`, each with a test both ways; `canvas_ui.svg_bar`/`svg_ring` fixed; `pp.py` YAML lint fixed | A screen is not done until it has been opened in Studio and walked in **every state and screen**, with the longest sample values. |

## 2. Process lessons

- **Get a Studio-built reference at the start.** Ask for it at G1 (`/ingest`): even one hand-built screen of the real app proves the layout. If there is none, build with
  `canvas_ui.py` and expect Studio to find things; budget a round for it.
- **Studio is the only layout oracle, and it reports in layers**: property errors, then names, then YAML, then formulas once the data sources are bound. Fix each pasted batch, rebuild,
  bump the version (PA-T11), and say plainly that more may follow.
- **Durable guards belong in `tools/`.** `specs/_working/` is git-ignored: a project script that holds a guard loses it. Generic builders live in `tools/` (`canvas_ui.py`,
  `schema_builder.py`, `flow_builder.py`); project-specific generators stay in the project.
- **The sign-off rules are not negotiable.** Only the Client PO approves G2. Claude never sets it, and never rewrites the workbook after approval: a change after sign-off is a proposed
  change (`specs/acceptance-criteria/proposed-changes-<date>.md`) that people apply. A feature the PO asks for outside the criteria is built only with that proposal written.
  Record every scope decision in PROJECT.md section 3 (what is scope, which design version is accepted, geometry overrides).
- **Open questions carry a baseline** (what is built if nobody answers) and go to PROJECT.md section 4 and the workbook's Questions sheet. Approving with open questions is allowed; the build uses the baselines.
- **Interim mail**: a `MailOverride` environment variable lets Dev and Test send every message to one tester mailbox; Production leaves it blank. Never hard-code an address.
- **Order writes safely in flows**: send the email first, then move the status. A failed flow then leaves the record unchanged and can be re-run (flow-standard P8).
- **Collections in the shape the screens use.** Load lists into collections with `ForAll(<delegable Filter>, {Column: Source...})` so screens read plain text columns (`Status`), filter locally
  (`in` is a contains), and reload after every action. Patch by item ID, wrap writes in `IfError`, validate with `Notify`.
- **Schemas**: the importer takes at most 5 sample rows; the base `Title` column cannot be indexed from a schema (index it in list settings); a schema change after the lists exist needs
  the importer re-run and a data-source refresh; never change a field name or ID after creation.
- **Tenant facts stay 🔶** until the client's admin confirms them; never guess licensing, DLP, the service account or who imports into Production.
- **Do not repeat a failed approach more than once.** After the second UI failure the answer was to clone the working reference, not to refine the generator.

## 3. Environment notes (Claude Code on Windows)

- `python` in the Bash tool can resolve to a broken virtualenv. Run every tool as `uv run tools/<tool>.py`: uv uses the repository's own `.venv` with the pinned Python and packages. Set `export PYTHONIOENCODING=utf-8` if a glyph such as ☑ still crashes cp1252 output.
- Long Python in a Bash heredoc with backslashes or `\n` gets mangled (`\\n` becomes a real newline). **Write the script to a file with the Write tool, then run it.**
- `pac` has no offline formula compiler. `pac canvas unpack --layout SourceCode` and `pack` are the only offline tools; Studio finds the rest.
- A project folder that is not a git repository cannot be committed to: `git init` first, or the per-stage commits in `/deliver` cannot happen.
- Installing anything outside the repository changes the machine: show the command and ask first. `uv sync` writes only the repository's `.venv`, so it needs no asking; installing uv itself does.

## 4. Project start checklist

1. `/project-setup`, then **fill PROJECT.md** (tenant facts stay 🔶).
2. Put the inputs in `inputs/`, **including a Studio-built reference app of the real UI if one exists** (`samples/<app>/`), then `/ingest`. Check the
   prototype register (`specs/prototype-fidelity.md`) lists every view, including the ones a click reveals: the app replicates the prototype (CLAUDE.md §7).
3. `/acceptance-criteria`; the Client PO signs it off (G2), recording their name and date. Then `/deliver`.
4. Before G6: read `docs/standards/ui-patterns.md`. Screens come from the reference app or `tools/canvas_ui.py`; never hand-written.
5. After any build: open the app **from the imported solution** in Studio, add the data sources and flows, **Run OnStart**, press every button once, paste Studio's errors back.
6. After any schema change: importer again, refresh data sources.
7. Record each new problem here and add its guard.

## 5. Where the guards live

| Guard | File |
|---|---|
| The prototype as the UI's specification; the fidelity register | [standards/prototype-fidelity.md](standards/prototype-fidelity.md), `specs/prototype-fidelity.md`, `/verify` check 17 |
| The prototype measured as rendered; optionally each screen compared with its Studio screenshot | `tools/visual_compare.py`, `specs/visual-map.json`, `/verify` check 21 (reports only) |
| Layout rule, numbers, patterns, checklist | [standards/ui-patterns.md](standards/ui-patterns.md) |
| Screen builder (and self-test against the reference app) | `tools/canvas_ui.py`, `samples/powerapp/` |
| List schema builder | `tools/schema_builder.py` |
| Flow builder | `tools/flow_builder.py` |
| Worked example of cloning a reference app | `tools/examples/clone_reference_app.example.py` |
| Build-time checks (names, variants, YAML, lists, columns, flows) | `tools/pp.py build` |
| Formula checks (Microsoft's parser, then functions, names, properties, data, delegation, variables, flows, AC comments) and their tests | `tools/pp.py fx`, `tools/powerfx.py`, `tools/tests/`, [standards/powerfx-validation.md](standards/powerfx-validation.md) |
| Traps PA-T1 to PA-T27, T-1 to T-25 | [standards/powerapps-traps.md](standards/powerapps-traps.md) |
| Skills that enforce it | `.claude/skills/scaffold`, `ui-dev`, `design-spec`, `functionality-dev`, `verify` |
