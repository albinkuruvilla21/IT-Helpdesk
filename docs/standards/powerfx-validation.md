# Power Fx formula validation

**Mandatory.** Every Power Fx formula in `canvas/<App>/Src/*.pa.yaml` is validated while it is written and again before release.
This standard says how, what each check proves, and what nobody may claim until Studio and the running app have confirmed it.
It applies to Claude and to people alike, in every stage that touches a formula (G6 `/scaffold`, G7 `/ui-dev`, G8
`/functionality-dev`, G9 `/flows` where an app calls a flow, G11 `/verify release`) and to ad-hoc fixes.

The checks live in [`tools/powerfx.py`](../../tools/powerfx.py) and run inside `uv run tools/pp.py build` and `uv run tools/pp.py fx`.
Traps are cited as `PA-T…` / `T-…` ([powerapps-traps.md](powerapps-traps.md)), rules as `L…` and sections of
[dev-standards.md](dev-standards.md).

---

## 1. The four levels: what is proven, and what you may say

A formula Studio refuses **does nothing when it runs, and says nothing** (PA-T26, PA-T27). So validation is staged, and each level
proves only its own row:

| Level | Proven by | Run by · when | Afterwards you may say | You may **not** say |
|---|---|---|---|---|
| **1 · Syntax** | **Microsoft's Power Fx parser** (`Microsoft.PowerFx.Core`, shipped inside `pac`), through `tools/fxparse.ps1` | `pp.py fx` after every edit; `pp.py build` | "parses" | "works", "compiles" |
| **2 · Static meaning** | The analyser in `tools/powerfx.py` (§3): functions, arity, behaviour, names, properties, enums, types, list columns, Patch, delegation, variables, flows, AC comments | Same | "no defect found by the static checks" | "error-free", "compiles" |
| **3 · Studio** | Power Apps Studio binds every name and type: the app opened **from the imported solution**, lists and flows added, **App checker → Formulas: 0 errors**, no delegation warning, **Save**, **Publish** | A person · end of G7, G8, every release candidate | "compiles in Studio (version, date)" | "works" |
| **4 · Run time** | The acceptance checks walked on the Dev site with real lists; the test cases (G10) | A person · G8, G10 | "AC-… passes" (for the checks walked) | anything about checks not walked |

Rules:

1. **Never call a formula "error-free", "working" or "validated"** on the strength of levels 1–2. Say what ran: *"`pp.py fx`:
   0 errors, syntax confirmed by Microsoft's parser 1.99; not yet opened in Studio"*.
2. **Level 1 must be Microsoft's parser** for a stage to finish. If the build reports `syntax checked by the stdlib parser only`,
   fix the toolchain (§7) or say so in the stage report; the stdlib parser is a fallback, not the authority.
3. Levels 3–4 need a person. Inside `/deliver` they go on the outstanding list; run alone, ask for them. Until they are done the
   report says **"not yet opened in Studio"** (CLAUDE.md §10).

## 2. When to run what

| Moment | Command | Must be |
|---|---|---|
| After every change to a `.pa.yaml` (seconds; no packing) | `uv run tools/pp.py fx` | 0 errors. Read every warning; fix it or say why not |
| Before marking G6, G7 or G8 `Done`, and after any fix | `uv run tools/pp.py build` | 0 errors (it runs the same formula checks on the packed app, plus the solution checks) |
| After changing `tools/powerfx.py`, `tools/fxparse.ps1` or `tools/powerfx-functions.json` | `uv run python -m unittest discover -s tools/tests` and `uv run tools/powerfx.py --selftest` | All pass; the Studio-built sample stays free of Studio-class findings |
| Release (G11, `/verify release`) | `uv run tools/pp.py fx --release`, then `/verify` | 0 errors: `TODO(AC-…)` stubs and mock data are errors here |
| Release, in Studio (level 3) | App checker → **Formulas**, **Rules**, **Accessibility**, **Performance** | 0 errors; every delegation warning fixed |

## 3. What the static checks cover

`E` = error (the build fails), `W` = warning (reported; judge it). An error is used only where the rule is certain: Studio refuses
the formula, or a repository rule forbids it. Everything else is a warning.

| Code | Checks | Sev. | Source of truth | Limits |
|---|---|---|---|---|
| `FX-SYNTAX` | The formula parses; `;` chaining only in behaviour properties | E | Microsoft's parser ([overview](https://learn.microsoft.com/en-us/power-platform/power-fx/overview)) | Locale: source is invariant (`,` and `;`) |
| `FX-YAML` | Every property value starts with `=`; a ` #` in an unquoted value is a YAML comment, so the formula is cut there (shows as `FX-SYNTAX`) | E | pa.yaml format; PA-T25 | Full YAML parse only with PyYAML installed |
| `FX-PARSER` | Microsoft's parser accepts a formula the analyser cannot read: levels 2 checks were **skipped** for it | W | — | Report it; extend the analyser |
| `FX-FUNC` | Every function exists (case-sensitive), including `Calendar.`/`Clock.` and user-defined functions in `App.Formulas` | E | [Canvas formula reference](https://learn.microsoft.com/en-us/power-platform/power-fx/formula-reference-canvas-apps); Microsoft's engine | Connector actions (`Office365Users.…`) are checked only as far as the connector is a known data source |
| `FX-ARITY` | Argument counts | E | `tools/powerfx-functions.json`: generated from Microsoft's engine; canvas-only functions from each function's syntax | Overload-specific argument types are not checked |
| `FX-BEHAVIOR` | Functions that change state (`Set`, `Patch`, `Navigate`, `Notify`, `SubmitForm`, `'Flow'.Run`, …) only in behaviour properties (`On…`), never in a named formula; a `{ … }` user-defined function only from behaviour properties | E | [Behavior formulas](https://learn.microsoft.com/en-us/powerapps/maker/canvas-apps/working-with-formulas-in-depth) | — |
| `FX-NAME` | Every name resolves: control, screen, global / context variable, collection, named formula, list in `schemas/`, data source, flow, enumeration, `Self`/`Parent`/`ThisItem`/`ThisRecord`. Context variables belong to one screen. `Navigate` to a screen; form functions on a form; `Reset`/`SetFocus` on a control; `Refresh` on a data source | E | [Working with formulas](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/working-with-formulas); [screens and context](https://learn.microsoft.com/en-us/powerapps/maker/canvas-apps/add-screen-context-variables) | A bare name inside the record scope of a table whose columns are unknown (a collection, a connector result) is **not checked**; the build counts them |
| `FX-THISITEM` | `ThisItem` only inside a gallery, a form or a list control's item properties | E | [Operators](https://learn.microsoft.com/en-us/power-platform/power-fx/formula-reference-overview) | — |
| `FX-CTRLPROP` | `control.Property`, `Self.X`, `Parent.X` exist on that control type | E | Studio's control templates (the app's `References/Templates.json`, then `tools/canvas-control-templates.json`); [property reference](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/reference-properties), [modern controls](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/modern-controls/modern-controls-reference) | Controls with no packed template (data cards, code components such as `Text@0.0.51`) are not checked |
| `FX-ENUM` | Members of enumerations this check knows completely (`NotificationType`, `ScreenTransition`, `DisplayMode`, `SortOrder`, `Align`, `FontWeight`, layout enums, …); text where an enumeration is expected | E | Canvas function and control references | `Color`, `Font`, `Icon` and other open enumerations: name only |
| `FX-TYPE` | A **literal** of the wrong type for the property: text in `Align`, `Width`, `Color`, `Visible`; a scalar in `Items`; a record in `Text`. Also `IfError` whose protected chain ends in `ClearCollect`/`Collect`/`Filter`/`ForAll` (a table) and whose fallback ends in `Notify`/`Set`/`Reset` (a boolean): end the chain with `; true` (PA-T31) | E/W | Property reference; Studio | Other types of expressions are Studio's job (level 3) |
| `FX-TEXT` | A text literal that is really a formula (`="User().FullName"` shows those words), or a lone quote mark (`=""""`) | W | — | Heuristic, so a warning |
| `FX-SCHEMA` | Every list a formula names has `schemas/<List>.csv`; every column read (`List.Col`, `ThisItem.Col` in a gallery of that list, a column in `Filter`/`LookUp`) or written exists (internal or display name) | E | `schemas/*.csv`, parsed as XML | The **site** may still lack it (PA-T27): re-run the importer, refresh the data source |
| `FX-PATCH` | `Patch`/`Collect`/`Update`/`UpdateIf` on a list: no read-only column (`ID`, `Created`, `Author`, calculated); a Choice takes `{Value: "…"}` with one of its choices (T-11); a Person takes a record; numbers, Yes/No, dates of the right kind; `Defaults()` of the same list; required columns on create (W) | E/W | [Patch](https://learn.microsoft.com/en-us/power-platform/power-fx/reference/function-patch); the CSV | Values that are expressions are not typed |
| `FX-ERRHANDLING` | A write to a list inside `IfError(…)`, or `Errors(<List>)` read, or `App.OnError` set; `SubmitForm` to a form with `OnFailure` | W | dev-standards §5; [forms](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/working-with-forms) | — |
| `FX-DELEG` | On a list in `schemas/`: `Search`, a function on the column (`Lower(Title)`), `in`/`exactin` with a column, a Note or calculated column, sorting by a formula (E); `IsBlank`, Person/multi-value columns, column-to-column comparisons, aggregates (`CountRows`, `Sum`, `ForAll`, `Distinct`, …) over the list (W) | E/W | dev-standards §5; PA-T14 | Only where the table **is** a list (directly, or through `Filter`/`Sort`/`SortByColumns`). Studio's blue delegation warning is the authority |
| `FX-INDEX` | Every column a `Filter`, `LookUp`, `Sort` or `SortByColumns` on a list uses is `Indexed="TRUE"` (except `ID`) | E | L5, T-1, T-9 | — |
| `FX-NAV` | `Navigate` in a screen's `OnVisible` or in `App.OnStart` (PA-T30) | E | Studio's message "Navigate cannot be used here..." | Not in `OnSelect` or other `On…` properties |
| `FX-NAME` (Split) | `Result` used inside `Filter`, `LookUp` or similar over a `Split(...)` table (PA-T38): Studio does not know that column name | E | Studio's "Name isn't valid. 'Result' isn't recognized" | The column's real name is not checked: test values with `in` instead |
| `FX-ARG` | `ShowColumns` or `DropColumns` given column names as text (PA-T33) | E | Studio's "Expected identifier name" | Other functions that take identifiers |
| `FX-VAR` | `Set` takes a variable name, never a named formula, control, screen or list; one type per variable (literals compared); not both a variable and a collection; global and context variable of the same name (W) | E/W | [Variables](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/working-with-formulas) | Types of non-literal values are not compared |
| `FX-UNUSED` | A global variable set and never read | W | dev-standards §10 | — |
| `FX-FLOW` | `'Flow name'.Run(…)` names a flow in `solution/src/Workflows`; the arguments match its Power Apps (V2) trigger's inputs (required and total) | E | The flow's JSON | V1 (`PowerApp`) triggers: arguments not checked. The flow must still be **added to the app** in Studio (PA-T26) |
| `FX-AC` | `// AC-<PROJECT>-NN.n` cites its check number (W); an AC ID inside a text string, which users would see (E); a formula that is only a comment (E in a behaviour property, W elsewhere); `TODO(AC-…)` stubs (W, E with `--release`); mock data at release (E) | E/W | dev-standards §9; CLAUDE.md §10 | That the ID exists in the workbook is `ac_workbook.py check` (`/verify` check 5) |
| `FX-TOKEN` | No `RGBA(…)` or `ColorValue(…)` on a screen | E | D11 | — |
| `FX-DUPNAME` | A control name used on two screens | E | PA2110 (control names are app-wide) | Same-screen duplicates: PA-T23 check |
| `FX-IGNORE` | An `fx-ignore` that is not allowed or has no reason | E | §5 | — |

Every run ends with counts (formulas, calls, names checked, names in record scope **not** checked, list queries, writes). A large
"not checked" count means more depends on Studio (level 3).

## 4. Writing formulas that pass

These are the rules the checks enforce. Write to them; don't write and wait for the build.

**YAML and syntax**
- Every value starts with `=`. A value containing `: ` is single-quoted; a value containing ` #` must be quoted too (or YAML cuts it).
  Multi-line formulas use `|-`. Comments never contain `: ` (CLAUDE.md §10).
- `;` chains actions, in `On…` properties only. A data property is one expression.

**Functions and names**
- Names are case-sensitive: `Notify`, not `notify`; `true`, not `True`. Use only the functions in the [canvas formula
  reference](https://learn.microsoft.com/en-us/power-platform/power-fx/formula-reference-canvas-apps), and the argument count it gives.
- Behaviour functions (`Set`, `Collect`, `Patch`, `Navigate`, `Notify`, `SubmitForm`, `Reset`, `'Flow'.Run`, …) go in `On…`
  properties only. Named formulas (`App.Formulas`) are pure; a reusable action is a user-defined function with a `: Void = { … }` body.
- Read a control's real property from its template: a classic text input is `.Text` (not `.Value`), a dropdown is
  `.Selected.Value`, a gallery is `.Selected` / `.AllItems`.
- Enumerations, not text: `Align.Center`, `DisplayMode.Edit`, `NotificationType.Error`, `ScreenTransition.None`.
- Text is text and a formula is a formula: `Text: =User().FullName`, not `="User().FullName"`; an empty text is `=""`.

**Variables** ([working with formulas](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/working-with-formulas))
- Global: `Set(gblName, value)`. Screen-scoped: `UpdateContext({locName: value})`, or `Navigate(scr, ScreenTransition.None, {locName: value})`.
  A context variable exists only on its screen.
- One type per variable: don't `Set` a number in one place and text in another. Never `Set` a named formula; derive it instead (D5).
- Prefer named formulas for anything derived (dev-standards §10); `OnStart` stays small (PA-T18).

**Lists** ([forms](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/working-with-forms), dev-standards §4–§5)
- Name a list by its list name (`CON_SiteRequest`) and its columns by the CSV's internal name (or display name in quotes).
- Reads: `Filter`/`LookUp` with `=`, `<>`, `<`, `>`, `<=`, `>=`, `&&`, `||`, `!` and `StartsWith(Column, value)`, on **indexed**
  columns. Compute the value side, never the column side: `Created >= DateAdd(Today(), -7)`, not `DateAdd(Created, 7) >= Today()`.
  No `Search`, `in`, `Lower(Column)`, Note or calculated columns. Sort by a column (`SortByColumns`), not a formula.
- Counting or summing a whole list (`CountRows(List)`, `Sum(List, …)`) runs in the app over at most 500 items: use a filtered
  query, or store the figure.
- Writes: `IfError(Patch(List, Defaults(List) | record, {…}), Notify("<what failed>", NotificationType.Error))`, or the form's
  `OnFailure`. Never write `ID`, `Created`, `Modified`, `Author`, `Editor` or calculated columns. Choice: `{Value: "Open"}`
  with a value on the column. Person: a record with `Claims`. Required columns on every create.

**Flows**
- `'Flow display name'.Run(arg1, …)`, in behaviour properties, with the V2 trigger's arguments. Add the flow to the app in Studio
  from inside the imported solution (PA-T26).

**Traceability** (dev-standards §9)
- End the formula with `// AC-<PROJECT>-NN.n`, the check number included. Never inside a text string; never at the start of a
  single-line formula (it would comment out the whole formula); inside the YAML quotes when the value is quoted.

## 5. Suppressing a finding

Only judgement findings may be suppressed: `FX-DELEG`, `FX-INDEX`, `FX-ERRHANDLING`, `FX-TEXT`, `FX-UNUSED`. Put the reason, and
who agreed, in a comment in that formula:

```yaml
Items: =Filter(CON_Holiday, Year(HolidayDate) = Year(Today())) // fx-ignore FX-DELEG list capped at 60 items by design, agreed PO 2026-10-26
```

A suppression is still printed, as a warning, on every build; `/verify release` lists every one in the release notes' known issues.
Syntax, function, arity, behaviour, name, property and enumeration errors cannot be suppressed: fix them.

## 6. What the static checks cannot prove

Say these plainly in every stage report that touches formulas; they are why levels 3 and 4 exist.

| Not proven statically | Proven by |
|---|---|
| Types inside expressions (`"a" + 1`, a record where a table is expected), and the columns of collections, variables and connector results | Studio (App checker → Formulas) |
| That the lists, columns and flows exist **on the site and in the app** (PA-T13, PA-T26, PA-T27) | Studio, after binding the lists and adding the flows |
| Properties of code components and data cards (no packed template); variant-specific properties (PA-T21) | Studio, on open |
| Delegation where the table is not directly a list, and Studio's own delegation verdict | Studio's blue delegation warning: treat as an error |
| Permissions, real data, time zones, locale formats, concurrency, performance | Walking the acceptance checks on the Dev site; App checker → Performance |
| That the behaviour is the prototype's | The prototype comparison (prototype-fidelity §7) |

**The Studio pass (level 3)**, at the end of G7 and G8 and for every release candidate: import the unmanaged ZIP into Dev; open the
app **from the solution**; bind the lists and add the flows; **Run OnStart**; open **App checker** and fix every *Formulas* and
*Rules* error and every delegation warning; **Save**, **Publish** (PA-T8); `pp.py export`. Any error Studio shows that `pp.py`
missed is a gap in the checks: fix the formula, then follow §8.

## 7. Toolchain

| Part | What | If it is missing |
|---|---|---|
| `pac` (PROJECT.md §1) | Ships `Microsoft.PowerFx.Core.dll`: Microsoft's parser. Found under the dotnet tool store or `%LOCALAPPDATA%\Microsoft\PowerAppsCLI`; `PP_POWERFX_DLL` overrides | Syntax falls back to the stdlib parser and the build warns |
| PowerShell 7 (`pwsh`), on the same .NET major version as `pac` (pac 2.13 → .NET 10 → PowerShell 7.6) | Loads the DLL (`tools/fxparse.ps1`). Windows PowerShell 5.1 cannot | Same fallback, same warning |
| `tools/powerfx-functions.json` | Function names and arity: `core` generated from Microsoft's engine, `canvas` from the formula reference, `behavior` list | When `pac` is upgraded (D12): `uv run tools/powerfx.py --refresh-functions`, review the diff, run the tests |
| `tools/tests/test_powerfx.py` | Every rule tested both ways; parser cross-checked against Microsoft's; the sample app as a corpus | — |

## 8. When Studio finds what the checks missed

1. Fix the formula.
2. Add a failing test to `tools/tests/test_powerfx.py` (the defect fires; the correct formula stays quiet), then the rule in
   `tools/powerfx.py`, and prove it by breaking something on purpose (lessons-learned row 12).
3. Make it an error only if the rule is certain; otherwise a warning.
4. Run the tests and `--selftest`: the Studio-built sample must stay free of Studio-class findings.
5. Add a row to §3, and a trap to `powerapps-traps.md` (CLAUDE.md §10).

## 9. Microsoft references

- [Power Fx overview](https://learn.microsoft.com/en-us/power-platform/power-fx/overview) ·
  [formula reference overview](https://learn.microsoft.com/en-us/power-platform/power-fx/formula-reference-overview) ·
  [formula reference for canvas apps](https://learn.microsoft.com/en-us/power-platform/power-fx/formula-reference-canvas-apps)
- [Working with formulas](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/working-with-formulas) ·
  [behavior formulas in depth](https://learn.microsoft.com/en-us/powerapps/maker/canvas-apps/working-with-formulas-in-depth)
- [Control property reference](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/reference-properties) ·
  [modern controls reference](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/controls/modern-controls/modern-controls-reference)
- [Working with forms](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/working-with-forms) ·
  [screens and context variables](https://learn.microsoft.com/en-us/powerapps/maker/canvas-apps/add-screen-context-variables) ·
  [canvas apps documentation](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/)
