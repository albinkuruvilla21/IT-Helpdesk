---
name: functionality-dev
description: Stage G8. Replaces the canvas app's mock data with the real SharePoint lists, implements the business rules as named formulas, writes with Patch/forms, permission and error handling, traced to acceptance criteria IDs, and lists the Studio steps that bind the lists. Use when the user runs /functionality-dev, optionally naming screens.
argument-hint: "[screen names — default: all, in build order]"
disable-model-invocation: true
---

# /functionality-dev: stage G8

You make each screen work against real lists, criterion by criterion. **The acceptance checks are
the specification.** Implement exactly them, cite them, and raise anything they don't settle. Don't
invent behaviour. **Where a check leaves a detail open, the prototype settles it** (CLAUDE.md §7): its
validation rules and the moment they fire, its messages verbatim, its sort orders, filters, derived
values and their formats, what each action does next. Read the prototype's script for the screen, and
its rows in `specs/prototype-fidelity.md`.

## 0. Before you start

- `PROJECT.md` §2: **G7 must be `Done`.**
- The lists on the dev site, and bound to the app in Studio, are needed to *test* this stage, not to
  write it. Formulas name each list by its list name (`CON_SiteRequest`), which is the data source's
  name once a person adds it (PA-T13). Run alone, ask whether that is done; inside `/deliver`, don't
  ask. Either way carry on: §2 check 4 goes on the outstanding list.
- Screens: `$ARGUMENTS`, or all, in build order. G8 → `In progress`.

## 1. For each screen

Read: its AC rows and checks (`uv run tools/ac_workbook.py dump …`) · its build-plan entry (and §1.1: any reference code it starts from, in `references/`) ·
`specs/data-model.md` for its lists · the CSVs · `docs/standards/dev-standards.md` §3–§5, §8–§9 ·
`docs/standards/powerapps-traps.md` (PA-T13, PA-T14, T-1, T-9, T-10) · `docs/standards/ui-patterns.md` §6 (the data and behaviour patterns: role in `OnStart`, **collections in the shape the screens use**, one reload block, writes by item ID, `IfError` everywhere) · **`docs/standards/powerfx-validation.md` §4 "Lists", "Variables", "Flows"** (the rules the build enforces on reads, writes and calls).

**Reads:** replace each mock collection with a **delegable** query on the list, loaded into a collection **in the shape the screens already use** (ui-patterns §6), so the screens' formulas do not change:
- `Filter`/`Sort`/`LookUp` only with delegable operators, only on **indexed** columns (check the CSV:
  `Indexed="TRUE"`), and never on Person, calculated or Note columns (PA-T14, T-10).
- Column names are the CSV's internal names.
- Loading: `LoadingSpinner: =LoadingSpinner.Data` on the screen; empty: the empty label's `Visible`
  from `IsEmpty(<the query>)`.

**Writes:** `Patch` or `SubmitForm`, always with failure handling:
`IfError(Patch(CON_X, …), Notify("<what failed, in the user's words>", NotificationType.Error))`, or the
form's `OnFailure`. Never send read-only columns. A new item's ID comes back from `Patch`; a reference to
it is that number in the referring list's `<Target>Id` column (L2, L3).

**Permission:** a refused save (403) shows "You don't have access", and no retry (STD-PERM). Don't hide
controls as the access control (D6); shaping the UI for a role is fine, from a named formula
(`IsApprover`).

**Rules:** replace every `TODO(AC-…)` with the rule it names, keeping the AC ID (with check number) in
the comment. A rule used on two screens is a named formula (D5).

Remove `Mock<Entity>` and `MockState` once nothing uses them.

If a check needs a column the CSV doesn't have, that's a schema change: append the field following
`/list-schemas` (append only; never alter an existing field), update `specs/data-model.md`, and run
`uv run tools/check_schemas.py`. Never add it on the site by hand. If the lists already exist on a site,
say they need re-importing and the app's data source refreshing.

If a check is ambiguous and the prototype doesn't settle it, implement the narrowest reading, mark it
`// AC-… assumes <x>, see Q-nn`, and add the question to PROJECT.md §4.

Then compare each behaviour row in the register (validation, action, navigation, conditional, list,
derived, role) with what the formulas now do, against the prototype's script (prototype-fidelity §7).
Fix differences; update *Built as* and Status.

**After each screen: `uv run tools/pp.py fx`**, 0 errors. On this stage's formulas these warnings are not left standing: `FX-DELEG`
(a query SharePoint can't run, so it sees only the first 500 items), `FX-ERRHANDLING` (a silent failed save), `FX-PATCH` (a required
column missing on create), `FX-FLOW` and `FX-UNUSED`. Fix each; where the rule truly doesn't apply (a list capped by design), suppress it
in that formula with `// fx-ignore <code> <reason, who agreed>` (powerfx-validation §5) and list it in the report.

## 2. Check

1. `uv run tools/pp.py fx`, then `uv run tools/pp.py build`: 0 errors, *syntax confirmed by Microsoft's Power Fx parser*. Every
   `FX-SCHEMA` and `FX-INDEX` error means the CSV and the formula disagree: fix the formula, or change the schema under `/list-schemas`'s
   rules, never the check.
2. `grep -rnE "Mock[A-Z]|MockState|TODO\(AC" canvas/*/Src`: nothing left for the screens you did.
3. `uv run tools/ac_workbook.py check specs/acceptance-criteria/<CODE>_AcceptanceCriteria.xlsx --src canvas --src solution/src`:
   no errors, and no "not referenced" warning for these screens' live criteria.
4. **In Studio, then on the dev site** (needs a person and the lists): import the unmanaged ZIP into Dev;
   open the app **from the solution**; turn on *Automatically create environment variables when adding
   data sources*; add each list (Data → Add data → SharePoint → the dev site → the list); add each flow the build names (PA-T26);
   **Run OnStart**; **App checker → Formulas: 0 errors and no delegation warning** (level 3, powerfx-validation §6); **Save**,
   **Publish**; `uv run tools/pp.py export`; then walk each screen's
   acceptance checks (give them the checklist from the dump). Fix what fails. Inside `/deliver`, put it
   on the outstanding list with the checklist.

## 3. Finish

When all screens are done: PROJECT.md G8 → `Done`. Reply with: per screen, the checks implemented and
any assumptions (with Q-ids), the lists each needs bound in Studio, and whether the walk-through is
still outstanding. **Formula validation, as the level reached** (powerfx-validation §1): the build's formula line (list queries and
writes checked, names in record scope not checked), every remaining warning and every `fx-ignore` with its reason, then
level 3 (App checker) and level 4 (checks walked) as done, with who and when, or outstanding. Never "the formulas work" before level 4.
