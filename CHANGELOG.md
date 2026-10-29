# Changelog

Newest first. A project made from this template records here which template version it started from,
then its own material changes above that line.

## IT Help 1.0.2.0 — 2026-10-29 (the first Studio pass: UI glitches and one formula error)

Fixed from the delivery team's video: the form's dropdowns on every screen (PA-T41), the ticket table's pills, headings and pager (PA-T43 to PA-T45), SVG bars with
no fill (PA-T40), cut-off text (PA-T46) and `{Name: Name}` on Attachments (PA-T42). New guards: `FX-OVERLAY`, `FX-SVG` and an Attachments check in `tools/powerfx.py`, each tested
both ways. Traps PA-T40 to PA-T48 and lessons-learned row 18 written here and in the boilerplate (template 1.10.0, branch `from-it-help-2026-10-29`, 67ce3cd).

## IT Help 1.0.0.0 — 2026-10-29 (delivery G0 to G11, from template 1.9.0)

Acies Innovations IT Help: a canvas app (Overview, ticket lists, create/edit form, ticket panel, knowledge base, Settings), nine SharePoint
lists, three notification flows, 44 acceptance criteria (43 live), 185 test cases. Built from the accepted prototype `inputs/design/index (4).html`.
Not yet opened in Studio. PO decisions applied: no delete (Q-11), no phone layout (Q-04), roles from `ITH_UserRole` (Q-03), no demo features (Q-05).

### Lessons to send back to the boilerplate (CLAUDE.md section 12; not yet pushed: the delivery lead agrees first)
- `pp.py` YAML lint rejected Studio's own `LayoutMaxHeight: =` (PyYAML cannot construct the bare `=`): fixed in `tools/pp.py` (`_Loader`).
- `prototype_design.py` did not map short custom-property names (`--ac`, `--c`, `--bd`, `--tx`, `--mu`, `--h`...) nor a dark scheme switched by
  `[data-theme=dark]`; and it infers the prototype's content width from the largest `max-width` (an article column here), giving a wrong scale
  (pass `--content` equal to that width for scale 1.0). Fixed the first two, with a self-test; the third needs a `--proto-content` option.
- `test_ac_workbook.test_sample_passes` traced the sample workbook against the delivered project's own app; it now does so only while the starter app is present.
- `canvas_ui.py` has no icon-button, wrapped-grid or sidebar-with-folding pattern; `tools/ith_ui.py` has one for each (icon image with `OnSelect`; a Gallery with `WrapCount`).
- Control names are unique across the **whole app** (FX-DUPNAME), not per screen: an overlay repeated on every screen needs a per-screen prefix.
- A comment (`// ...`) inside a formula that is concatenated into another formula hides what follows it on the line: compose with a `tail` before the comment.
- Environment-variable display names for lists must equal the list name (PA-T32), and a column the app sorts by must be indexed (FX-INDEX), including master-data `SortOrder`.

## Template 1.9.0 — 2026-10-28 (the prototype measured in a browser, and compared with Studio)

`prototype_design.py` reads the prototype's CSS as text, so it can't apply the cascade or inheritance, and doesn't see a
view a script draws; and "Matched" in the fidelity register rested on a person looking at two screens side by side.
Adapted from the Acies SPFx template's `visual_diff.py`. A canvas app can't be rendered outside Power Apps, so the build
side is a Studio screenshot.

### Added
- **`tools/visual_compare.py`**: `measure <screen>` renders the prototype in Chromium and reports each view's text (font,
  px and points, weight, line height, colour, position) and boxes (fill, radius, border, shadow, padding, size) in the
  app's units, per state and colour scheme, with the clock frozen; `run [--strict]` renders every mapped view and compares
  it with its Studio screenshot (share of differing pixels, shape, a prototype | Studio | difference image, a report);
  `compare` does two images without a map.
- **`specs/visual-map.json`** (G3 `/design-spec`, completed at G7): each screen × state × scheme, its prototype region,
  the `setup` script that opens the view, its screenshot in **`specs/screenshots/`** (committed: the evidence for
  `Matched`), and any accepted difference citing design-spec §9. Sample: `samples/design/SAMPLE-prototype.html` and
  `SAMPLE-visual-map.json`.
- **`/verify` check 21** (optional, reports only, never blocks a release): each entry `matches`, is `accepted` or `differs`;
  a missing screenshot is "not yet compared in Studio". Measuring needs no screenshots; comparing is a recommended extra.
- Tests: `tools/tests/test_visual_compare.py` (images both ways; with Chromium: frozen clock, script-drawn view, dark
  scheme, inherited type, scale, and `run` matching, differing, accepted and missing).

### Changed
- `/design-spec` writes the map and measures each view as rendered (the rendered value wins over the CSS reading);
  `/ui-dev` builds to `measure`, and its Studio pass saves screenshots and runs the comparison; `/deliver`'s G7
  outstanding item says the same. prototype-fidelity §4 (`Matched` needs the comparison), §7 and §8; pipeline G3;
  CLAUDE.md §1 and §9; lessons-learned §5.
- `/project-setup` and README *Setting up the Python tools*: `uv run playwright install chromium` once per machine.

**Dependencies.** `playwright` (Apache-2.0, Microsoft) with Chromium, and `pillow` (MIT-CMU), in `pyproject.toml`:
developer tooling, not shipped.

**Not changed here:** `.claude/settings.json` should allow `Bash(uv run tools/visual_compare.py:*)` and
`Bash(uv run playwright install chromium)`; Claude Code does not edit its own permissions, so add them by hand.

## Template 1.8.0 — 2026-10-28 (what the SPFx template learned, adapted)

The improvements the Acies SPFx template (0.5.0–0.8.0) made that apply to Power Apps. Browser measuring of the
prototype and screenshot comparison (SPFx `visual_diff.py`) are not in this release.

### Changed
- **AC IDs are `AC-<PROJECT>-NN`**: the project code, then one running number for the whole project (`AC-CON-01`,
  `AC-CON-02`, …), cited `AC-CON-07.3`. This is the testing team's format across projects. `ac_workbook.py check`
  rejects an AC ID whose code is not the workbook's project code; `powerfx.py` (`FX-AC`) and the traceability
  check accept codes of up to 10 letters and digits. `TC-<AREA>-NNN` is unchanged. The sample workbook, starter app,
  starter flow, templates and standards are renumbered. Tests: `tools/tests/test_ac_workbook.py`, `test_ac_project_code_ids`.
- **The tools run through uv.** `pyproject.toml` lists the packages once (dependency group `tools`), `uv.lock` pins
  them, `.python-version` pins Python 3.12, which uv downloads itself. Every `python tools/…` is now
  `uv run tools/…`. `tools/requirements.txt` is gone; `.venv/` is ignored. **PyYAML is now a dependency**, so
  `pp.py build` always parses every `.pa.yaml` in full (PA1001), and warns when it can't. `pp.py doctor` reports uv
  and PyYAML. `/project-setup` runs `uv sync` instead of asking to change the user's Python. README: *Setting up
  the Python tools*. Without uv: `pip install --group tools` (pip 25.1+).
- **`.claude/settings.json`** allows the checks the rules require after every edit: `pp.py fx`,
  `prototype_design.py`, `figma_pull.py`, the self-tests and the unit tests. `import`, `export`, `check`, `setup`
  and `reset_template.py` still ask.
- **Lessons go back to the boilerplate in the same session** (CLAUDE.md §12, and a row in §9): what goes back and
  where (a trap, a check with its tests, a `canvas_ui.py` pattern, refreshed control templates, a rule, a tool fix),
  how (a clone beside the project, a version bump, the boilerplate's checks), and what doesn't (client values; the
  project's own screens and flows go to the catalogue). A project is its own repository; `/reset-template` is the
  fallback for one built inside the template.
- **The design from Figma.** `tools/figma_pull.py` (standard library; `pages`, `pull`, `images`) reads the accepted
  design through Figma's API, with `specs/figma.json` naming the file, page and app scale, and a read-only token
  outside the repository. `values.md` gives type in Power Apps points and lengths at the app's scale. inputs/README
  *The design*: HTML prototype first, then the Figma file; never an HTML converted from a PDF or images.
  `ingest.py` prints a **PROTOTYPE GAP** when the design can't be measured, and `/ingest` records the question.
  `/design-spec` and prototype-fidelity §3 read Figma. Tests: `tools/tests/test_design_inputs.py`.
- **Release ZIPs are committed** to `releases/` by `/verify release` (`G11: release <version>`), with
  `releases/README.md`. `dist/` stays ignored. `reset_template.py` removes a project's release ZIPs.
- **The project gets its own README.** README.md's introduction and getting-started section are marked
  (`<!-- README:intro -->`, `<!-- README:start -->`); `pp.py setup` swaps them for
  `docs/templates/project-readme.template.md` (client, code, solution, prefix, app, *Joining this project*).
  `reset_template.py` restores the template's README. Tests: `tools/tests/test_project_readme.py`.
- **Inputs are committed at G1** (`G1: inputs`), unless secrets were found, the contract keeps the documents off
  GitHub, a file is over 50 MB, or a client solution in `other/` is unreviewed. `/status` reports inputs not yet
  committed; `/project-setup` commits G0.
- `docs/pipeline.md` names the catalogue, Figma, the prototype gap and `releases/` at their stages.

**Dependencies.** [uv](https://docs.astral.sh/uv/) (MIT or Apache-2.0, Astral): developer tooling, not shipped.
`pyyaml` (MIT), previously optional.

**Note for `/reset-template`:** it restores the starter files from the git tag `template-starter`. Move that tag to
this version's commit, or a reset brings back the 1.7.0 PROJECT.md, README and sample IDs.

## Template 1.7.0 — 2026-10-28 (the reuse catalogue)

Ported from the Acies SPFx template (0.5.0), adapted to Power Apps. A project now looks up what Acies has already built before it builds a
screen or a flow, and gives back what it built. The catalogue is its own repository,
[acies-powerapps-catalogue](https://github.com/Acies-Innovations/acies-powerapps-catalogue) (empty until the first project contributes).

### Added
- **`tools/catalogue.py`** (`fetch`, `list`, `search`; standard library only) and `tools/catalogue.config.json`. The clone is `references/_catalogue/`,
  git-ignored. Tests: `tools/tests/test_catalogue.py`.
- **`/catalogue` skill** (`search`, `suggest`, `contribute`). `contribute` records the `pac` and Studio versions (D12), the connectors (D2) and whether
  the app was opened in Studio, and asks before opening the pull request.
- **PROJECT.md** §1 *Code ownership* (Acies by default) and §8 *Reuse*. **Build plan** §1.1 *Reuse of existing work*: one row per screen,
  component and flow (*Pattern*, *Adapt code*, *No match*, *Not used*).
- CLAUDE.md §2, §8 and §9; README *The reuse catalogue*; PROMPTS.md.

### Changed
- `/project-setup` fetches the catalogue and asks about code ownership; `/ingest` suggests matches (new §3b); `/build-plan` decides every piece;
  `/scaffold`, `/ui-dev`, `/functionality-dev` and `/flows` read the reference code §1.1 names; `/deliver` drafts catalogue entries after G11.
- `.claude/settings.json` allows `python tools/catalogue.py`; `.gitignore` ignores `references/`.

## Template 1.6.2 — 2026-10-28 (lessons from the TimesModern project, and a clean reset)

The second project built from 1.6.1 added these to the template. The project's own changelog entries are not kept here; its history
is in git.

### Added
- **`tools/canvas_ui.py`:** `side_nav` (left navigation with brand, logo tile and an icon per page), `avatar`, `svg_bar`, `svg_icon`,
  and row options on `table` (`row_fill`, `row_pad`, `row_gap`). Documented in `docs/standards/ui-patterns.md`. The self-test still
  matches the reference sample.
- **PA-T39 (trap and library check):** a short `ModernText` (a badge under 24 high) with default padding shows a scrollbar, and
  `AlignInContainer.Start` means top in a horizontal row. `Screen.yaml()` now refuses a `ModernText` under 24 high without
  `PaddingTop: 0`. The fix is `AlignInContainer.Center`, `AutoHeight` and zero padding.

### Changed
- `tools/tests/test_prototype_fidelity.py`: `test_real_prototype_if_present` is generic (type scale non-empty, pt and label heights
  positive), so it no longer pins one prototype's selector.
- The project's generators are examples: `tools/examples/timesmodern_*.example.py` (the reset moves them there).

## Template 1.6.1 — 2026-10-27 (lessons from the TimesheetModern project, and a clean reset)

The first project built from 1.5.0 found these gaps in the template. The project's own changelog entries are not kept here; its history
is in git.

### Added
- **PA-T38 (trap, `FX-NAME` check):** `Result` is not the column of a `Split` table in Studio. `pp.py fx` flags it; the trap gives the
  `in`-over-`Split` replacement. Test pair in `tools/tests/test_powerfx.py`.
- **Reset: `deployment/settings.template.json`** is removed by `tools/reset_template.py`, because a project creates it at G11.
- **Tests:** `tools/tests/test_prototype_fidelity.py` finds any HTML prototype in `inputs/design/`, so it no longer depends on one file name.

### Fixed
- **Starter screen (`canvas/StarterApp/Src/scrHome.pa.yaml`):** four `FX-TEXT` defects shipped with the template. A quote mark was shown
  as text in three places, and `User().FullName` was shown as words. They are now `=""` and `=User().FullName`.
- **Dashboard pattern lessons** (for any dashboard built with `canvas_ui.py`): a KPI caption and its percentage need explicit heights
  (`h=20`, `valign="Middle"`) or Studio clips them; an empty-state label belongs inside its card, not above it; a user label with a blank
  name must not show a stray separator.

### Changed
- The project's generators are examples: `tools/examples/timesheetmodern_*.example.py` (the reset moves them there).

## Template 1.6.0 — 2026-10-27 (the app matches the prototype's look, not only its structure)

The second project's app passed every check and opened in Studio looking nothing like the accepted prototype: the template told screens
to use the reference app's sizes and chrome, colours were picked by hand, and rounded corners, shadows and translucency were wrongly
recorded as "not native". The prototype's look is now measured and built.

### Added
- **`tools/prototype_design.py`**: reads an HTML prototype's CSS and reports the colours of **every scheme** (`:root` and
  `@media (prefers-color-scheme: dark)`) mapped to token names, contrast with the nearest compliant shade, the type scale converted to
  Power Apps points (px × scale × 0.75) with label heights, and every radius, padding, gap, height, shadow, gradient and font, scaled to
  the app. `--formulas` proposes the `App.Formulas` block; `--check` compares an app's tokens with the prototype (`/verify` check 20).
- **`canvas_ui.py` prototype patterns** (ui-patterns §10): `Design` (pt, scaled lengths, label heights, text widths), `floating_topbar`
  (rounded translucent bar, segmented pill tabs, logo tile), `panel`, `svg_image`, `svg_ring`, `svg_backdrop`, `svg_tile`; `box` and
  `section` take radius, translucent fill, border colour and shadow; `button(radius="pill")`; `badge(radius, size)`;
  `Screen.backdrop` and `body_fill`; `tokens_block(dark=, hexes=)` writes `IsDark`, `If(IsDark, dark, light)` tokens and `Hex<Name>`
  texts for SVG. Existing defaults are unchanged (`--selftest` still identical to the reference app).
- `tools/tests/test_prototype_fidelity.py`: properties against Studio's templates, formulas through the checks (Microsoft's parser
  confirmed all 129 pattern formulas), measuring and the `--check` mode both ways.
- prototype-fidelity §8 (visual fidelity, measured), ui-patterns §10, register kind `style`, build-plan spike **S-UI** until the
  patterns are proven in Studio, lessons-learned row 17.

### Changed
- CLAUDE.md D11 and §7 rule 5: with no brand guide the prototype's colours are the brand **in every scheme**; sizes are measured
  from the prototype, the reference numbers only where it gives none.
- prototype-fidelity §5 and §6: chrome, cards, backgrounds, rings, pills and schemes map to the new patterns; only backdrop blur,
  following the device's light/dark setting automatically and unavailable fonts remain platform limits.
- design-standards §3 (scheme, surface and `Hex` tokens), §8; design-spec template (both schemes, measured type scale and geometry);
  skills `/ingest`, `/design-spec`, `/scaffold`, `/ui-dev`, `/verify` (check 20).

## Template 1.5.0 — 2026-10-27 (lessons from the first delivered project, and a reset skill)

The first full `/deliver` run (G0 to G11) was opened in Studio three times. Each error Studio showed is now a check and a trap, and the
library gained what the prototype needed.

### Added
- **`/reset-template` skill and `tools/reset_template.py`**: turn a delivered project back into this clean template (dry run first; the
  starter files come from the git tag `template-starter`; the project's generators move to `tools/examples/`).
- **Checks** in `tools/powerfx.py`, each with a test both ways: `FX-NAV` (`Navigate` in `OnVisible` or `OnStart`), `FX-TYPE` for `IfError`
  with a table on one side and a boolean on the other and for a modern dropdown's `Default` that is not a record, `FX-ARG` (`ShowColumns`
  with text column names), `FX-ENUM` for `ErrorKind.EditPermission`, `CreatePermission` and `DeletePermission` (Studio does not know them);
  `FirstError` and `AllErrors` are in scope in `IfError` fallbacks and `App.OnError`.
- **`pp.py build`** fails a list environment variable whose display name is not its list name (Studio names the data source after it).
- **Traps PA-T30 to PA-T37** and **lessons-learned rows 14 to 16**: Navigate in OnVisible, IfError types, data-source naming, ShowColumns
  and ErrorKind, dropdown Default, one broken OnStart colouring the app, sections that do not fit their content, header title wrapping.
- **`tools/canvas_ui.py`**: `topbar()` (a single-band header with tabs), `body()` and `Screen` take a content width and a top.
- **`tools/examples/timesheet_ui.example.py` and `timesheet_flows.example.py`**: a complete project generator (three screens, collections, validation,
  flows, a CSV export) as a worked example. Delete them if not wanted.

### Changed
- `canvas_ui.table_header()` and `modal_frame()` wrote quoted text as `""File Name""`; fixed. `section()` no longer suggests a height of `None`.
- The starter screen (`scrHome`) is the corrected one (no quote marks, no words in place of `User().FullName`).
- `test_starter_app_is_clean` requires no errors (a delivered app keeps agreed suppressions as warnings).
- ui-patterns §4 and §7: sections always have an explicit, formula-driven height.

## Template 1.4.0 — 2026-10-26 (Power Fx formula validation)

Every formula is now validated while it is written and before release, and nobody calls one "working" on the strength of static checks.
`pac canvas pack` never parsed formulas, so a misspelt function or a formula written as text built, imported and failed silently in the app.

### Added
- **`docs/standards/powerfx-validation.md`** (mandatory): the four levels (Microsoft's parser, static meaning, Studio, run time) and what
  may be claimed after each; when to run what; every check with its source and limits; how to write formulas that pass; suppression with a
  reason; what static checks cannot prove; the Studio pass; extending the checks.
- **`tools/powerfx.py`**: a Power Fx tokenizer, parser and analyser for the pa.yaml source. Checks function names and argument counts,
  behaviour functions outside `On…` properties, names (variables, context variables per screen, collections, controls, screens, lists,
  flows, enums), control properties against Studio's templates, enumeration members, literal types, list columns, `Patch` (read-only,
  Choice, Person, required columns, `Defaults`), delegation and indexes on SharePoint lists, variable types, flow calls against the V2
  trigger, and acceptance-criteria comments. Findings are `FX-…` codes; errors only where the rule is certain.
- **`tools/fxparse.ps1`**: runs **Microsoft's own Power Fx parser** (`Microsoft.PowerFx.Core`, shipped inside `pac`) through PowerShell 7,
  so syntax is Microsoft's verdict, not a regex's. Falls back to the stdlib parser, with a warning, when `pac` or `pwsh` is missing.
- **`tools/powerfx-functions.json`**: function arities generated from Microsoft's engine (`python tools/powerfx.py --refresh-functions`),
  plus the canvas-only functions from the formula reference, and the behaviour-function list.
- **`python tools/pp.py fx [--release]`**: the canvas checks on source in about a second, without packing. `pp.py doctor` reports
  whether Microsoft's parser loads.
- **`tools/tests/test_powerfx.py`** (35 tests): every rule both ways, the parser cross-checked against Microsoft's, and the Studio-built
  sample (3,284 formulas) as a corpus that must stay free of Studio-class findings.
- Traps **PA-T28** (a label shows a formula's words or a quote mark) and **PA-T29** (a well-formed but wrong formula packs and is refused in
  Studio); lessons-learned row 13.

### Changed
- `pp.py build` / `validate` run the formula checks on the packed app; they replace the regex-based list, `Patch`-column and flow-name
  checks (same messages for PA-T26 and PA-T27).
- **Fixed in the starter app and `canvas_ui.chrome()`**: the header user label was `="User().FullName"` (it showed those words), and the
  header band, navigation strip and tab underline were `=""""` (a quote mark). `chrome()` now treats `user_expr` as a formula and emits `=""`.
- CLAUDE.md (§1, §2, §9, §10, §11), `/ui-dev`, `/functionality-dev`, `/verify` (checks 6, 10, 16; new 18 and 19; release gate and notes),
  `/scaffold`, `/flows`, `/deliver`, `dev-standards.md` §5, §9, §10, §12, README (PowerShell 7 prerequisite, commands, troubleshooting).

## Template 1.3.0 — 2026-10-21 (the prototype is the UI specification)

The accepted prototype (typically HTML) is now the primary reference for the app's UI, layout, design, interactions and functionality. The app translates it with native controls; it never redesigns, simplifies or omits what the prototype demonstrates, except for a recorded platform limitation or client decision.

### Added
- **CLAUDE.md §7 "The prototype is the UI specification"** (former §7–§10 are now §8–§11).
- **`docs/standards/prototype-fidelity.md`** — how to inspect a prototype (its source and scripts, not only the conversion), how its parts become native controls, what counts as a platform limitation, how the build is validated against it.
- **`docs/templates/prototype-fidelity.template.md`** → `specs/prototype-fidelity.md`: the fidelity register, one `P-nn` row per element or behaviour, from inventory (G1) through AC mapping (G2) to `Built` / `Matched` / `Deviation` (G7–G8).
- **`/verify` check 17** — no register row `Not built` after G7; deviations justified; `Built` rows reported as "not yet compared in Studio".

### Changed
- `/ingest` reads the prototype's source and writes the register; `/acceptance-criteria` maps every row to a criterion (messages quoted) or records why not; `/design-spec`, `/build-plan`, `/scaffold`, `/ui-dev`, `/functionality-dev`, `/deliver` and `/status` build from and check against it.
- `design-standards.md` §2 (the prototype settles detail the AC leaves open) and §8 (what must match exactly); `ui-patterns.md` (what versus how; the prototype's chrome; validation as the prototype shows it); `dev-standards.md`; D11 (positions and proportions from the prototype, text and control heights from `ui-patterns.md`).
- `design-spec` template §9 cites P-IDs and allows only prototype-fidelity §6 reasons.

## Template 1.2.0 — 2026-10-21 (what the first project taught)

The first project (a request-and-approval app: six screens, six flows) found every problem below. Each is now guarded. Read `docs/lessons-learned.md` once at the start of a project.

### Added
- **`docs/lessons-learned.md`** — every failure, its root cause, what now guards against it; process lessons; Windows / Claude Code notes; the project start checklist.
- **`docs/standards/ui-patterns.md`** — the rule (never invent a layout), the skeleton, every pattern with its numbers, data and behaviour patterns, what breaks Studio, a checklist.
- **`tools/canvas_ui.py`** — screen builder encoding the reference app's layout; `--selftest` rebuilds parts of `samples/powerapp` and compares them (0 differences).
- **`tools/schema_builder.py`**, **`tools/flow_builder.py`** — list schemas and cloud flows from Python, with the rules built in; both have `--selftest`.
- **`tools/examples/clone_reference_app.example.py`** — worked example of cloning a Studio-built reference app into a project.
- **`samples/powerapp/`** — a Studio-built reference app (`.msapp` and unpacked `Src/`). It is a request-and-approval app built from a client prototype, so its wording belongs to that project; use it for layout only.
- **Traps PA-T21 to PA-T27** in `powerapps-traps.md`.

### Changed
- **`pp.py build` now fails** on a duplicate control name (PA-T23), `LayoutMode` / `Layout` on a container or gallery variant (PA-T21), invalid YAML syntax (PA-T25), and a list or written column that a formula uses but `schemas/` lacks (PA-T27). It **warns** about every flow the app calls (PA-T26).
- **D11**: colours through tokens only; layout sizes are the plain numbers of `ui-patterns.md` (computed sizes produced layouts that failed in Studio).
- Skills `/scaffold`, `/ui-dev`, `/design-spec`, `/functionality-dev`, `/verify` (checks 15 and 16) and `/ingest` (asks for a Studio-built reference) enforce the above; `design-standards.md`, `dev-standards.md` (layout skeleton), `pipeline.md` and the design-spec template agree.
- `tools/canvas-control-templates.json` refreshed from a Studio-saved app (ModernDropdown 1.0.3 and others).
- The starter app is now one screen (`scrHome`) built with `canvas_ui`; the colour tokens in `App.Formulas` are the library's.

## Template 1.1.1 — 2026-10-20

### Fixed (confirmed: the ZIP imported and the app opened in Studio, 2026-10-20)

- **Studio couldn't open the re-imported app: `ErrOpeningDocument_UnknownError`.** The template's
  `.msapr` had no `Controls/1.json`, the root App/Host control every Studio-saved app has; it now
  carries a generic one. `validate` warns when an app lacks it. (PA-T20)
- **`build` stamps `AppVersion` with the build time** (staged copy only), so each re-import is a new
  app version, as a Studio save would be. (PA-T19)
- `build` also writes `dist/<App>.msapp`, to open directly in Studio (**Open → Browse**) without
  importing a solution.
- **The solution ZIP is the deliverable.** The importer chooses environment variable values and
  connections in the portal's import wizard. `deployment/settings.<env>.json`, `pp.py settings` and
  `pp.py import` are optional (scripted imports only); docs and skills no longer require them.
- The "open in Studio once" warning (PA-T8) now reads `packed.json` (`LoadFromYaml`) instead of guessing
  from missing controls.

## Template 1.1.0 — 2026-10-20

**Same structure as the Acies SPFx template, and a fix for the first live import.**

### Fixed

- **The starter app failed to open in Studio** after a successful import:
  `error PA2108 : Unknown property 'AccessibleLabel' for control type 'Classic/Button@2.2.0'`. A classic
  button has no `AccessibleLabel` (its `Text` is its accessible name); `pac canvas pack` doesn't check
  properties, Studio does. The button now uses `Tooltip`. (PA-T17)
- **`pp.py build` now checks every canvas control property** against Studio's own control templates:
  the app's `References/Templates.json`, then `tools/canvas-control-templates.json` (17 control types
  from Studio 3.26091). Verified: it flags the original error; it reports **no** false positives across
  the 1,498 controls of a Studio-saved reference app (container-provided layout properties are allowed;
  code-component controls are reported as not checked).

### Added: the SPFx template's structure

- **Pipeline G0–G11** with the one PO sign-off at G2 (`docs/pipeline.md`), `PROJECT.md` stage table,
  and **14 Claude Code skills** in `.claude/skills/`: `/project-setup`, `/ingest`,
  `/acceptance-criteria`, `/deliver`, `/design-spec`, `/build-plan`, `/list-schemas`, `/scaffold`,
  `/ui-dev`, `/functionality-dev`, `/flows`, `/test-cases`, `/verify`, `/status`. `PROMPTS.md` with
  Power Apps supporting prompts (Studio errors, changes made in Studio).
- **`inputs/`** (brd, transcripts, design/prototype, branding, other) and **`specs/`**, as in SPFx.
- **`schemas/`** with the SPFx list importer and `tools/check_schemas.py`, unchanged: the list schema
  standard is shared.
- **`tools/`**: `ingest.py` (unchanged), `ac_workbook.py` (column *Power Apps Component*; `check --src`
  traces AC IDs through canvas YAML and flow step notes, repeatable), `pp.py` (moved from `scripts/`;
  `setup` takes `--code`, `--list-prefix`, `--dev-env`, `--dev-site`).
- **Standards** in `docs/standards/`: dev (YAML rules, the checkable control list and which controls
  have `AccessibleLabel`), design (tokens as named formulas, mapping a design onto screens), flow
  (flows as solution components), acceptance criteria and list schema (from SPFx), and
  `powerapps-traps.md` (PA-T1–T18 plus the SharePoint list traps under their SPFx `T-` numbers).
- **Templates**: build plan, design spec, release notes (Power Apps), data model (from SPFx).
- **Samples**: an AC workbook for a fictional *Site Requests* app whose `AC-HOME-01/02` and
  `AC-NOTIFY-01` trace into the starter app and flow; the starter flow; the SPFx list schema exemplar.
- The starter app and flow carry AC IDs (`// AC-HOME-01.1`, a flow step's notes).

### Changed

- `docs/standards.md` → `docs/standards/dev-standards.md` + `design-standards.md`;
  `docs/traps.md` → `docs/standards/powerapps-traps.md`; `scripts/pp.py` → `tools/pp.py`.

## Template 1.0.0 — 2026-10-20

First version of the Acies Power Apps delivery template.

- **Solution source** (`solution/src/`, SolutionPackager format): Acies publisher (`acies_`), a canvas
  app, an automated cloud flow, three environment variables (SharePoint site + list, text) and two
  connection references (SharePoint, Office 365 Outlook). Standard connectors only.
- **Canvas app source** (`canvas/StarterApp/`, `pac canvas` SourceCode layout): one screen, design
  tokens as named formulas. Its `.msapr` holds only Studio's generic scaffolding: no data sources,
  assets or connections.
- **`pp.py`**: `doctor`, `setup`, `bump`, `build`, `validate`, `settings`, `import`, `export`, `check`.
- **Deployment settings** per environment; docs for ALM, standards, traps and the reference analysis.
- Verified offline with `pac` 2.13.1. The unmanaged ZIP then **imported successfully** into a live
  environment (2026-10-20), which exposed the PA2108 error fixed in 1.1.0.
