---
name: ui-dev
description: Stage G7. Builds the canvas app's screens to match the accepted design and the design spec, against mock data, in every state, at every width, to WCAG 2.1 AA, as canvas YAML that passes pp.py build. Use when the user runs /ui-dev, optionally naming screens.
argument-hint: "[screen names — default: all, in build order]"
disable-model-invocation: true
---

# /ui-dev: stage G7

You build what the user sees, against the **mock data** (`Mock<Entity>` named formulas), so the UI
can be seen and checked before any list is bound. Data rules belong to `/functionality-dev`. Purely
visual behaviour (tabs, expand/collapse, dialogs, focus order) belongs here.

**The accepted prototype is the primary reference** (CLAUDE.md §7, `docs/standards/prototype-fidelity.md`).
Translate it; don't redesign it. Its appearance, layout, user flows, validations and behaviour are
replicated with native controls as closely as the platform allows. Nothing it demonstrates is
simplified or left out unless the AC excludes it or a platform limitation forces it (prototype-fidelity
§6), and then it is a recorded deviation.

## 0. Before you start

`PROJECT.md` §2: **G6 must be `Done`** (and G3, which it implies). Screens: `$ARGUMENTS`, or all of
build-plan §1 in build order. Set G7 → `In progress`.

## 1. For each screen

`uv run tools/visual_compare.py measure <screen> [--state …] [--scheme …]` gives the prototype's rendered values for the
screen (type in points, lengths at the app's scale): build to those. Read **`docs/standards/ui-patterns.md` and `docs/standards/prototype-fidelity.md` first** (and build-plan §1.1: any reference screen it starts from, in `references/`), then: **the screen's view in the
prototype source** (markup, CSS and the script functions behind it, not only the converted text) and its images (look at them) ·
its rows in `specs/prototype-fidelity.md` · its design-spec §6 entry · its AC checks · `docs/standards/design-standards.md` §5–§8 ·
`docs/standards/dev-standards.md` §2, §6–§7 · **`docs/standards/powerfx-validation.md` §1, §4** (how every formula is written and what may
be claimed about it).

Build, in `canvas/<App>/Src/scr<Name>.pa.yaml`, **with `tools/canvas_ui.py` or by cloning the Studio-built reference app (`samples/<app>/Src/`)**. Never write a layout by hand
and never compute a size from a token:
- **What the prototype shows**: every region in its order, every control (the same kind, prototype-fidelity §5), every label and message
  verbatim, its proportions scaled to the base width, its navigation, interactions and visible states. Each register row for the screen is
  built, or is a deviation with its reason.
- **The skeleton** of `ui-patterns.md` §3: header and navigation placed on the screen, one scrolling auto-layout body, sections with explicit heights, tables as a gallery in a
  fixed-height `ManualLayout` wrapper, `ModernText` badges, segmented buttons, dialogs as controls over an overlay.
- **Controls from the checked list only** (dev-standards §2). A control the design needs that isn't there: a pattern the sample does not have is a spike (`ui-patterns.md` §9).
- **Colours are tokens**; **sizes are the prototype's, measured** (`specs/prototype-design.json`, design-spec §3–§4) through
  `canvas_ui.Design`, the reference numbers only where the prototype gives none. A colour missing from the tokens: add a token
  (`App.Formulas`, design-spec §2 "Added tokens").
- **The look** (ui-patterns §10, prototype-fidelity §8): the prototype's chrome (`floating_topbar` or the pattern that matches it), card
  surfaces with its radius, fill, border and shadow, its background (`svg_backdrop`), rings and decorations as SVG, pill buttons and
  badges, in each scheme. "The library's default looks different" is never a reason to keep it.
- **All states**: loading, empty, error with the reason (including "You do not have access"), reachable on sample data so a reviewer can see them.
- **Keyboard and screen reader**: an accessible name on every interactive control, `Live` on labels that announce changes; status always in words as well as colour.
- Visual behaviour with variables (`Set(varModal, "aon")`): `Set`, `Navigate`, `Notify` only in `On…` properties; one type per variable;
  context variables (`UpdateContext`) only on their own screen (powerfx-validation §4).
- **After each screen: `uv run tools/pp.py fx`** (seconds, no packing). 0 errors before the next screen. Warnings are read, not skipped:
  `FX-TEXT` (text that should be a formula, a stray quote mark) and `FX-AC` (an AC ID without its check number, inside a string, or
  commenting out a formula) are fixed now; anything else is fixed or said in the report.

## 2. Check

1. `uv run tools/canvas_ui.py --selftest`, then `uv run tools/pp.py build`: 0 errors (duplicate names, `LayoutMode`/`Layout` on a variant, YAML syntax and every formula are checked: powerfx-validation §3). Fix every `unknown property` with the control's real property. The build must say *syntax confirmed by Microsoft's Power Fx parser*; if it says the stdlib parser was used, fix the toolchain (powerfx-validation §7) or say so.
2. No literals on screens. Expected: no output.
   ```bash
   grep -nE "RGBA\(|ColorValue\(|#[0-9A-Fa-f]{6}\b" canvas/*/Src/scr*.pa.yaml
   ```
3. Contrast: any colour pairing you introduced is in design-spec §2 with a computed ratio.
4. **Compare with the prototype** (prototype-fidelity §7 and §8), screen by screen, **including the look**: `uv run tools/prototype_design.py <file>.html --content <w> --check canvas/<App>/Src/App.pa.yaml` 0 errors, then for each region its colours, type size and weight, radius, spacing, shadow and background against the measured design, in each scheme: re-read the view's source, then go region by region and
   row by row through its register rows against the YAML (order, controls, control types, wording, proportions, states), and walk
   each interaction (every click, every validation with bad input and its message, every navigation, every show/hide). Fix each
   difference in the screen (or the library) and compare again. Then set each row's *Built as* and Status `Built`; a difference you
   can't remove is `Deviation` with a design-spec §9 row whose reason prototype-fidelity §6 allows. No row for a done screen stays
   `Not built`.
5. **Open it in Studio** (needs a person; until then say "not yet opened in Studio"): the person pastes back every error Studio shows, and what **App checker → Formulas** reports (level 3, powerfx-validation §6). Fix the cause; for an error the static checks missed, add a test and a check (powerfx-validation §8) and a trap. Then, **optionally** (it needs screenshots from a person; skip it when nobody can take them, and leave the rows `Built`), the **visual comparison**: import the unmanaged ZIP into Dev (the portal: Solutions → Import), open the app in Studio, **Save**, **Publish** (PA-T8), then screenshot each
   screen's canvas (Preview, F5; no Studio chrome) at the app's size for every entry in `specs/visual-map.json` (each state and
   scheme), saved where the entry's `screenshot` says (`specs/screenshots/<screen>-<state>-<scheme>.png`). Then
   `uv run tools/visual_compare.py run` and **look at every** `specs/_working/visual/*.compare.png` (prototype | Studio |
   difference): list the differences, fix them, or record them as deviations in design-spec §9 and the entry's `accepted`.
   Rows whose screen `matches` (or is `accepted`) and that you checked on the image → `Matched`. A share under the tolerance
   can still hide a wrong word or colour, so the image decides, not the number. Run alone, offer it and
   ask for the screenshots; inside `/deliver`, put it on the outstanding list as optional and carry on.

## 3. Finish

When every screen is done: PROJECT.md G7 → `Done`. Reply with: screens done, the register counts by
status, deviations recorded (each with its reason), states you proposed, and anything a reviewer should
look at first. **Formula validation, as the level reached** (powerfx-validation §1): the `pp.py build` formula line (formulas, parser and
version, names not checked), its warnings, any `fx-ignore` with its reason, and "not yet opened in Studio" until a person has.
