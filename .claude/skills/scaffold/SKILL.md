---
name: scaffold
description: Stage G6. Creates every screen in the build plan as canvas YAML (header, body containers, navigation, state placeholders), the named formulas and mock data the screens need, and the solution components (connection references, variables), then removes the starter samples and verifies the build. Use when the user runs /scaffold.
disable-model-invocation: true
---

# /scaffold: stage G6

You give every screen in the build plan a correct, building skeleton, so `/ui-dev` and
`/functionality-dev` fill in rather than invent structure. The starter is the pattern; copy its
**shape**, not its content.

## 0. Before you start

`PROJECT.md` §2: **G4 and G5 must be `Done`.**

## 1. Read

`specs/build-plan.md` · `schemas/*.csv` · `docs/standards/ui-patterns.md` (**the layout rules**) · `docs/standards/dev-standards.md` §1–§3, §6, §9 (the YAML
rules and the **checked control list** in §2: use only those) · `docs/standards/design-standards.md` §4–§5 ·
the starter, every file: `canvas/<App>/Src/*.pa.yaml`, `solution/src/` (Solution.xml, Customizations.xml,
the variables, the flow), `pp.config.json`, and, for every piece build-plan §1.1 marks **Pattern** or **Adapt code**, the
reference files it names (`references/<repo>/…`; clone them at the recorded commit if the folder is missing, as `/build-plan` does).
Adapted code is brought to this repository's shape: our prefixes, our tokens, our data-source variables, only the controls and
connectors this project allows, and an AC ID on every formula. Never bring in a tenant URL, a list name, a GUID or a value from the
source project.

## 2. Shared layer, once

In `canvas/<App>/Src/App.pa.yaml` → `Formulas`, below the tokens:

- **Mock data**, one named formula per list: `Mock<Entity> = Table({ID: 1, Title: "…", <Field>: …}, …);`
  using the CSV's **internal names** as column names, built from the CSV's sample rows plus enough
  extra rows to show every state the design spec describes (long text, a missing value). Generate it
  from the CSVs with a script, not by hand. Add `MockState = "ready";` ("ready", "empty", "error",
  "loading") so a reviewer can see each state.
- **Named formulas** from build-plan §3, as stubs over the mock data with
  `// TODO(AC-XXX-NN.n) <rule>` for every rule left to `/functionality-dev`.
- `App.StartScreen` if the start screen isn't first in `ScreensOrder`.

## 3. Each screen, in build order

**Do not invent a layout.** Read `docs/standards/ui-patterns.md`, `docs/standards/prototype-fidelity.md`
and `samples/<app>/` first. Each screen's skeleton follows **the prototype's** view (design-spec §6):
its chrome, its regions in order, its navigation. The reference app and `canvas_ui.py` supply the
building technique, not the design.

- If the project has a **Studio-built reference app** (`samples/<app>/Src/`): clone it. Copy `tools/examples/clone_reference_app.example.py`, edit its mapping (colours to tokens, list and
  column names, the collections' shape, the actions) and run it. Keep every control, name, size and position. Add `Screens` to `Src/_EditorState.pa.yaml` → `ScreensOrder`.
- Otherwise build each screen with `tools/canvas_ui.py` (`Screen`, `chrome`, `title`, `card_row`, `section`, `field_row`, `segmented`, `table`, `modal_frame`, ...): the
  header and navigation placed on the screen, **one** scrolling body, sections with explicit heights, every table a gallery in a fixed-height wrapper. Write the
  generator script in `tools/` (committed), not in `specs/_working/`.
- Data is loaded into **collections in the shape the screens use** (ui-patterns §6); mock data is a collection filled by a named formula until G8.
- On data screens, the loading, error and empty messages exist from the start (they take no space while hidden).
- Colours are tokens (D11); sizes are the prototype's, measured (design-spec §3–§4, through `canvas_ui.Design`), the numbers in `canvas_ui.py` only where the prototype gives none; the chrome and surfaces follow ui-patterns §10. Every interactive control has an accessible name (a classic button's `Text`, an input's
  `AccessibleLabel`).
- Every screen cites its AC IDs in comments on the controls that implement them.

## 4. Solution components

- **Connection references** from build-plan §3: one `<connectionreference>` per connector in
  `solution/src/Other/Customizations.xml`, shaped like the starter's (`<prefix>_<connector>`), added to
  PROJECT.md §6.3.
- **Text variables** from build-plan §3: shaped like `<prefix>_SupportEmail` (type `100000000`).
- List variables were added at G5. Check each list in build-plan §2 has one.

## 5. Remove the samples

- `canvas/<App>/Src/scrHome.pa.yaml`'s starter content (replace it with the real home screen, or delete
  it and remove it from `ScreensOrder` if the build plan has no `scrHome`).
- The starter flow: `solution/src/Workflows/SampleNotifyOnNewItem-*.json` and `.json.data.xml`, and its
  `RootComponent type="29"` line in `Other/Solution.xml` (`samples/flows/` keeps a copy for `/flows`).
- `<prefix>_SampleList` and, unless the build plan uses it, `<prefix>_SupportEmail` (their folders),
  and their entries in PROJECT.md §6.2 (and in `deployment/settings.*.json`, if the project uses them).
- Connection references the build plan doesn't use.

## 6. Verify

1. `uv run tools/canvas_ui.py --selftest` passes, then `uv run tools/pp.py build`: **0 errors** (it also fails duplicate control names, `LayoutMode` / `Layout` on a variant and a comment after a closing quote). Every control is checked against Studio's templates; fix
   any `unknown property` by using the control's real property (dev-standards §2), never by editing the
   template file. Every formula is checked too (`docs/standards/powerfx-validation.md`): 0 errors; the `TODO(AC-…)` stubs show as
   `FX-AC` warnings until G7/G8 replace them, and fail at release.
2. `uv run tools/ac_workbook.py check specs/acceptance-criteria/<CODE>_AcceptanceCriteria.xlsx --src canvas --src solution/src`:
   no *errors*. Every screen's AC IDs should already be referenced by its comments and TODOs.
3. `grep -rnE "SampleList|SampleNotify|Say hello" canvas solution/src deployment`: nothing left.

## 7. Finish

PROJECT.md G6 → `Done`. Reply with the screen list, files created, components added and removed, and
anything in the build plan you couldn't scaffold and why. Suggest committing (`G6: scaffold`).
