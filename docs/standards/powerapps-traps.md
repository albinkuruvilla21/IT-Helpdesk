# Power Platform traps

Things that cost time on Power Apps deliveries, each with how to spot it and what to do. `pp.py
validate` catches the ones marked ✔. Add a trap when a project finds a new one.

| ID | Trap | Caught |
|---|---|---|
| PA-T1 | Building in the environment's default publisher | ✔ |
| PA-T2 | One environment variable per environment | ✔ (warning) |
| PA-T3 | A new connection reference for every flow | ✔ (warning) |
| PA-T4 | Current values shipped inside the solution | ✔ |
| PA-T5 | Dev values and IDs baked into flows | ✔ |
| PA-T6 | People hard-coded in formulas | ✔ |
| PA-T7 | Exports carry tenant data | partly |
| PA-T8 | An app packed from YAML hasn't been compiled | ✔ (warning) |
| PA-T9 | Flows after import: off, and owned by whoever imported | |
| PA-T10 | Unmanaged changes in Test or Prod | |
| PA-T11 | Version not raised | |
| PA-T12 | DLP splits the solution's connectors | |
| PA-T13 | A data source added without environment variables | |
| PA-T14 | Delegation limits on SharePoint | ✔ partly (`FX-DELEG`, `FX-INDEX` on lists in `schemas/`) |
| PA-T15 | No Dataverse, or the default environment | |
| PA-T16 | Settings-file connection IDs from the wrong environment | |
| PA-T17 | `pac` packs properties Studio refuses | ✔ |
| PA-T18 | A heavy `App.OnStart` | |
| PA-T19 | Re-importing an app with an unchanged `AppVersion` | `build` stamps it |
| PA-T20 | A `.msapp` without its App control: `ErrOpeningDocument_UnknownError` | ✔ (warning) |
| PA-T21 | Studio rejects a property the control's template lists, because it depends on the control's variant | ✔ (`LayoutMode`, `Layout`) |
| PA-T22 | A generated screen builds and imports but lays out badly in Studio (nested auto-layout with flexible heights) | |
| PA-T23 | Two controls on one screen share a name: `PA2110 An entity with name 'x' already exists` | ✔ (and across screens, `FX-DUPNAME`) |
| PA-T24 | `pp.py build` reports one error: `cannot access the file ... .zip because it is being used by another process` | |
| PA-T25 | `PA1001 YamlInvalidSyntax: did not find expected key` on open | ✔ |
| PA-T26 | A button that calls a flow does nothing and shows no message (red mark on the formula) | ✔ (warns) |
| PA-T27 | A button does nothing after a column or list was added to the source: the site and Studio still have the old schema | ✔ (checks the repo's schemas) |
| PA-T28 | A label shows the words of a formula (`User().FullName`) or a quote mark instead of its value | ✔ (warns, `FX-TEXT`) |
| PA-T29 | A formula that is wrong but well formed (a misspelt function, a behaviour function in `Text`, `txt.Value` on a classic input) packs and imports, and Studio refuses it on open | ✔ (`pp.py fx`, powerfx-validation.md) |
| PA-T30 | Studio: "Navigate cannot be used here since it would automatically always navigate away from this screen" on a screen's `OnVisible` | ✔ (`FX-NAV`, error) |
| PA-T31 | Studio: "Invalid argument type (Boolean). Expecting a Table value instead" on the `Notify` of `IfError(ClearCollect(...), Notify(...))` | ✔ (`FX-TYPE`, error) |
| PA-T32 | Formulas name a list `PRJ_Request`, but Studio calls the data source after the environment variable's **display name** (`Request list`), so every formula errors | ✔ (`pp.py build` fails a list variable whose display name is not its list name) |
| PA-T33 | Studio: "Expected identifier name" and "The function 'ShowColumns' has some invalid arguments"; "Name isn't valid. 'EditPermission' isn't recognized" | ✔ (`FX-ARG`, `FX-ENUM`) |
| PA-T34 | Studio: "Invalid formula. Expected a value compatible with 'Items'" on a modern dropdown's `Default` | ✔ (`FX-TYPE`) |
| PA-T35 | One bad formula in `App.OnStart` (or a named formula) makes dozens of unrelated errors on every screen that reads what it sets | Read the **first** error of App.OnStart before any other; fix it and re-open |
| PA-T36 | A card (section) is cut off: the last field, the table's rows or the buttons are missing, and the next card starts too early | ✔ (`section()` docstring, ui-patterns §7; no static check) |
| PA-T37 | The app title in the header wraps to two lines and is clipped | Header title width 250, tabs from 290 (`canvas_ui.topbar`) |
| PA-T40 | An SVG bar, ring or icon built by a formula draws nothing (a progress bar's fill is missing), with no error | ✔ (`FX-SVG`; `canvas_ui.svg_bar` and `svg_ring` use `Substitute(Text(Round(x, 2)), ",", ".")`) |
| PA-T41 | A dialog's dropdowns, inputs or buttons show on **every** screen state, over the content (the form's fields on the Overview) | ✔ (`FX-OVERLAY`) |
| PA-T42 | Studio: "Name isn't valid. 'Name' isn't recognized" on `ForAll(<item>.Attachments, {Name: Name})` | ✔ (`FX-NAME` on `Attachments`): the columns are `Id`, `DisplayName`, `Value`, `AbsoluteUri` |
| PA-T43 | A table's columns do not line up with its headings and the last cell of every row (an Edit button) is cut off: flexible labels and buttons in a row have a minimum width of about 136 px | `LayoutMinWidth: 0` on each flexible header button and row cell (`canvas_ui.table(..., fit=True)`) |
| PA-T44 | A status or priority pill inside a wrapper container disappears in a table row, so every later column in the row shifts left | Pill columns are fixed-width, the same in the header and in every row, and the pill sits directly in the row |
| PA-T45 | A pager or icon button of 34 px with text ("Previous page") shows "ious pag" | Use the prototype's icon as an Image with `OnSelect`, `AccessibleLabel`, `TabIndex: 0` and `DisplayMode` |
| PA-T46 | Text is cut off in a card or an empty state: a label with no width wraps in a centred column; a title that takes two lines in a one-line label | Give the label a `Width` and a height for the **longest** value's lines; check with the longest sample row |
| PA-T47 | A `// AC-…` comment inside a piece of formula that another formula includes hides everything after it on that line (a closing parenthesis, the next statement) | Compose with the comment last (`open_ticket(rec, tail)`); `pp.py fx` shows `Eof where ParenClose is expected` |
| PA-T48 | `pp.py build` says "not valid YAML ... tag:yaml.org,2002:value" on `LayoutMaxHeight: =` that Studio itself wrote | Fixed in `pp.py` (`_lint_yaml_syntax` constructs the bare `=`) |

SharePoint list and flow traps from the Acies SPFx template keep their `T-` numbers (end of this file),
because the list standard and dev-standards cite them.

---

### PA-T1 · Building in the environment's default publisher

**Symptom:** names start `new_` or `cr<3 chars>_`; the solution's publisher is
`DefaultPublisher<org>`. **Cause:** a solution created in the portal without choosing a publisher.
**Why it matters:** the prefix is permanent, and a component can't move publishers. Every project
built this way carries a meaningless prefix forever, and two projects in one environment collide.
**Fix:** this template's publisher (`setup --prefix`). Already built? Only a rebuild in a new
publisher fixes it, so catch it before the first import.

### PA-T2 · One environment variable per environment

**Symptom:** `X` and `TEST_X` side by side. **Cause:** treating a variable as a value rather than a
slot. **Fix:** one variable; a value per environment (`deployment/settings.<env>.json`). Twin
variables mean twin code paths, and the wrong one gets used in Prod.

### PA-T3 · A new connection reference for every flow

**Symptom:** `prefix_sharedsharepointonline_ea9e2`, `…_6d765`, `…_b5c7f` for one connector.
**Cause:** the flow designer creates a reference when a step's connection is picked rather than an
existing reference. **Fix:** one reference per connector (or one per *identity*, if some flows must
run as a different account), with a readable name. At import, each extra reference is another
connection to bind in every environment.

### PA-T4 · Current values shipped inside the solution

**Symptom:** `environmentvariabledefinitions/<name>/environmentvariablevalues.json` in the ZIP.
**Cause:** a variable's current value was in the solution when it was exported. **Why it matters:** an
environment that has no value of its own takes the packaged one: typically Prod pointing at the Dev
site. **Fix:** values live in `deployment/settings.<env>.json`. `pp.py export` deletes packaged
values; in the portal, *Remove from this solution* on the value before exporting.

### PA-T5 · Dev values and IDs baked into flows

**Symptom:** a flow parameter `"X (prefix_X)": {"defaultValue": "https://tenant.sharepoint.com/…"}`,
or an action input like `"source": "sites/tenant.sharepoint.com,<guid>,<guid>"`. **Cause:** the
designer writes the current value as the parameter default on export; file pickers (Excel Online,
SharePoint *Get file content*) store site and drive IDs. **Fix:** clear the defaults (`export` does);
give every site, list, library, drive and file path an environment variable and use it in the step.

### PA-T6 · People hard-coded in formulas

**Symptom:** `ClearCollect(colAllUsers, ["someone@client.com", …])` in `App.OnStart`. **Cause:**
quick access control. **Why it matters:** it puts personal data in source, changes need a release,
and hiding UI is not security (D6). **Fix:** a SharePoint list or Microsoft 365 group holds the
people; list permissions enforce access; the app only reads it to shape the UI.

### PA-T7 · Exports carry tenant data

**Symptom:** an exported `.msapp` holds the tenant's site URLs in `References/DataSources.json`,
connection IDs, and short-lived signed storage URLs (`…blob.core.windows.net/…&sig=…`) for embedded
images. **Cause:** normal Studio behaviour. **Fix:** keep the repository private; never paste an
export into a public issue; `validate` checks the app's YAML and the flows, not Studio's own
reference files.

### PA-T8 · An app packed from YAML hasn't been compiled

**Symptom:** `pac canvas pack` says *"must be validated first by opening the app for edit within the
Power Apps studio"*; users see errors. **Cause:** a YAML-packed `.msapp` carries source but not
Studio's compiled controls. **Fix:** after importing, open the app in Studio, let it load, **Save**,
**Publish**. Then `pp.py export`, so source holds the Studio-saved app.

### PA-T9 · Flows after import: off, and owned by whoever imported

Flows in this template import **off** (`StateCode 0`) so nothing fires before its variables are set.
Turn them on (`import --activate`, or in the portal). They are owned by the importing user and run on
the connections bound to their references: import Test and Prod as the **service account**, or bind
its connections. Flows that apps call need the app's users as *run-only users*, with *Provided by
run-only user* connections where the user's own identity should be used.

### PA-T10 · Unmanaged changes in Test or Prod

Editing a managed component in Test or Prod creates an unmanaged *active layer* on top. Later
upgrades import fine but stay hidden under it. Never fix in place; fix in Dev and release. To recover,
*Remove active customizations* on the component (solution layers view).

### PA-T11 · Version not raised

Importing an equal version is an update at best and is skipped with `--skip-lower-version`; a lower
version is refused for managed solutions. `pp.py bump` before every build that leaves Dev.

### PA-T12 · DLP splits the solution's connectors

A data loss prevention policy that puts SharePoint in *Business* and Outlook in *Non-business* (or
blocks one) suspends every flow that uses both, right after import. Check the target environment's
policy before the first import (PROJECT.md Q-02).

### PA-T13 · A data source added without environment variables

Adding a SharePoint list in Studio binds the app to that site URL unless the app setting
*Automatically create environment variables when adding data sources* is on (Studio → **Settings**;
Microsoft has moved it between releases). The app then reads Dev's list in every environment. Turn
it on before adding data sources, and add them from inside the solution.

### PA-T14 · Delegation limits on SharePoint

Formulas SharePoint can't evaluate server-side (`Search`, `in`, most string functions, `Filter` on
calculated or person columns) return only the first 500 rows (2,000 at most, app setting). Studio
shows a blue delegation warning; treat it as an error. Filter on indexed columns (root template
trap T-1).

### PA-T15 · No Dataverse, or the default environment

Solutions import only into an environment with a Dataverse database, even though the data stays in
Lists (D1). Don't use the tenant's *Default* environment for development or delivery: everyone in
the tenant is a maker there, and its default publisher invites PA-T1.

### PA-T16 · Settings-file connection IDs from the wrong environment

A `ConnectionId` in `deployment/settings.<env>.json` must be a connection **in that environment**
that the importing user may use. Get it with `pac connection list` while authenticated to that
environment. A wrong ID fails the import with a connection error.

### PA-T17 · `pac` packs properties Studio refuses

**Symptom:** the solution imports, but opening the app fails with `error PA2108 : Unknown property
'AccessibleLabel' for control type 'Classic/Button@2.2.0'` (or `PA2106` for a control version).
**Cause:** `pac canvas pack` checks the YAML's shape, not whether each property exists on the control;
Studio checks on open. A classic button really has no `AccessibleLabel` (its `Text` is its name).
**Fix:** `pp.py build` now checks every property against Studio's own control templates (the app's
`References/Templates.json`, then `tools/canvas-control-templates.json`). Use the controls in
dev-standards §2; anything else is a spike. Found on this template's first import, 2026-10-20.

### PA-T18 · A heavy `App.OnStart`

**Symptom:** the app takes seconds to show its first screen. **Cause:** `OnStart` collects lists and
sets dozens of variables before anything renders. **Fix:** named formulas (`App.Formulas`) for
derived values and tokens, `App.StartScreen` for routing, and each screen loads what it shows.

### PA-T19 · Re-importing an app with an unchanged `AppVersion`

**Symptom:** a re-imported app doesn't change, or fails to open. **Cause (a precaution, not separately proven):**
the app's `AppVersion` in `CanvasApps/<app>.meta.xml` is the version stamp Studio sets on every save;
a hand-built source never changes it, so a re-import could look like the same document; it was fixed in the same release as PA-T20, so which of
the two mattered wasn't isolated. **Fix:** `pp.py
build` stamps the build time into the staged copy. Source keeps its value; an export replaces it with
Studio's.

### PA-T20 · A `.msapp` without its App control

**Symptom:** the import succeeds; **Edit** fails with *Error opening file: ErrOpeningDocument_UnknownError*,
no detail. **Cause (most likely; fixed 2026-10-20 together with PA-T19, so not isolated):** a Studio-saved `.msapp` always holds `Controls/1.json`, the
root **App** control and its **Host** child. The YAML covers screens and App *properties*, not those root
objects. This template's first `.msapr` was stripped of every `Controls/*.json` (they held the reference
client's screens) and lost them too; the YAML parse passed (Studio got far enough to report PA2108), and
document load then failed. **Fix:** the template's `.msapr` now carries a generic App/Host control (the
reference app's, with its `OnStart` removed). `validate` warns when it is missing. After this fix the template's ZIP imported and opened in Studio. **If
it ever recurs:** make a blank canvas app in Studio, save it to this computer (`.msapp`), and use
`pac canvas unpack --layout SourceCode` on it as the baseline `.msapr`.

### PA-T21 · Studio rejects a property `pp.py build` accepts (variant-specific properties)

**Symptom:** the app imports, but opening it in Studio lists `error PA2108 : Unknown property 'LayoutMode' for
control type 'GroupContainer@1.5.0' and variant 'AutoLayout'` (and `'Layout'` for `Gallery@2.15.0` and variant
`Vertical`), while `pp.py build` passes. **Cause:** `tools/canvas-control-templates.json` lists a control's properties
across all its variants; Studio checks the variant actually used. An auto-layout container takes its mode from
`Variant: AutoLayout`, and a vertical gallery from `Variant: Vertical`, so neither takes `LayoutMode` / `Layout`.
**Fix:** leave those two properties out. Found on the first project, 2026-10-20, which also
confirmed that `Variant: Vertical` is accepted on a gallery. Other variant-specific properties may exist: open
every new screen in Studio before building on it.

### PA-T22 · A generated screen builds but lays out badly

**Symptom:** the app opens, but regions overlap, galleries are empty or tiny, or the page cannot scroll, although the YAML packs and
`pp.py build` passes. **Cause:** the first generated screens put the header, body and sections in auto-layout containers nested three
deep, gave galleries a flexible height (`FillPortions`, minimum heights) inside a scrolling container, and drew badges and dialogs as
containers. `pp.py` checks property names, not layout. **Fix:** use the skeleton a Studio-built app proves (dev-standards §2 "Layout
skeleton"): header and navigation placed on the screen, **one** auto-layout body below them, explicit heights, every table a gallery in a
fixed-height `ManualLayout` wrapper, `ModernText` badges, dialogs as controls over an overlay. Found 2026-10-20 by comparing with a
hand-built app of the same project (`samples/powerapp/`).

### PA-T23 · Two controls on one screen share a name

**Symptom:** opening the app lists `error PA2110 : An entity with name 'docHdr' already exists. Other definition located at …`.
**Cause:** names are built from a screen prefix plus a part name, and two parts collided (`doc` + `Hdr` for the header band, and a table
header row also called `docHdr`). `pac canvas pack` does not check names. **Fix:** `pp.py build` now fails on a duplicate name in a
screen. Give every control a name that is unique on its screen; a prefix scheme needs a different word for each part. Found
2026-10-21.

### PA-T24 · One `pp.py build` error about a ZIP "being used by another process"

**Symptom:** `build` ends with `1 error(s)` and `The process cannot access the file …\dist\<Solution>_<v>.zip`, or `SolutionPackager could
not unpack it`; the same build run again a few seconds later reports `0 error(s)`. **Cause:** on Windows another process (a virus scanner,
the file indexer) holds the freshly written ZIP while `pac solution unpack` round-trips it. **Fix:** wait a few seconds and run `build`
again. It is not a defect in the solution. If it fails twice in a row, look for something else holding the file. Seen on most builds
on the first project.

### PA-T25 · `PA1001 YamlInvalidSyntax` on opening the app

**Symptom:** Studio refuses a screen file with `error PA1001 : An error occurred while parsing PaYaml. Error code: YamlInvalidSyntax; Reason: While parsing a
block mapping, did not find expected key` and a line and column. **Cause:** the file is not valid YAML. On the first project a traceability comment
(`// AC-RESUB-01.5`) was appended **after** the closing quote of a single-quoted formula (a formula containing `: ` must be quoted). `pac canvas pack` does
not parse the YAML. **Fix:** put the comment inside the quotes. `pp.py build` now lints every `.pa.yaml` for text after a closing quote, and parses the whole
file with PyYAML (installed by `uv run`, from `pyproject.toml`; a warning when it is missing). Found 2026-10-21.

### PA-T26 · A button that calls a flow does nothing, and says nothing

**Symptom:** Submit (or any action button) does nothing when pressed, no `Notify`, nothing written to the list, and the formula has a red or yellow
mark. **Cause:** the formula contains `'Flow name'.Run(...)`. Until the flow is **added to the app**, the name does not exist, so Studio marks the whole
`OnSelect` as an error and runs none of it, not even the first validation message. A flow can only be added to an app opened **from the solution**
that contains it (an app opened as a loose `.msapp` has no flows). **Fix:** import the unmanaged solution ZIP into Dev, open the app from the solution, then
**Data > Add data > Flows** and add each flow the build lists. `pp.py build` names them in one warning. Found 2026-10-21.

### PA-T27 · A button does nothing after the schema grew

**Symptom:** as PA-T26, but the formula uses a column or a list that was added to `schemas/` **after** the lists were created on the site (the app's `Patch` or
`Filter` names `Reviewed`, or a new list `PRJ_Activity`). **Cause:** the site still has the old schema, and Studio keeps its own copy of each list's
columns. A name Studio does not know is an error, and the formula runs nothing. **Fix:** (1) run `schemas/import-lists.console.js` again on the site (it
adds missing columns and lists, and is safe to repeat); (2) in Studio, **Data**, the list's **...** menu, **Refresh** (or remove and add the data source);
(3) add any new list as a data source. `pp.py build` fails if a formula names a list or writes a column that is not in `schemas/`, so the repository is
consistent; the site and Studio still need steps 1 to 3 after every schema change.

### PA-T28 · A label shows a formula's words, or a quote mark

**Symptom:** the header shows the text `User().FullName` instead of the user's name; a header band or navigation strip shows a `"` in its
corner. **Cause:** a formula was written as text: `Text: ="User().FullName"` is the string of those words, and `Text: =""""` is a string
holding one quote mark (an empty text is `=""`). Both are valid Power Fx, so `pac`, Studio and the app accept them silently. The
template's own starter screen shipped with both, from `canvas_ui.chrome()` wrapping its arguments in quotes. **Fix:** remove the quotes from a
formula; write an empty text as `=""`. `canvas_ui.chrome()` now treats `user_expr` as a formula and emits `=""`; `pp.py fx` warns on a text
literal that parses as a formula using a known function or name (`FX-TEXT`). Found 2026-10-26.

### PA-T29 · A well-formed but wrong formula packs, imports, and is refused in Studio

**Symptom:** as PA-T26: a button does nothing, a label is blank, a red mark in Studio, or `pp.py build` passed and Studio lists formula
errors. **Cause:** `pac canvas pack` does not parse formulas at all. A misspelt or wrongly cased function (`notify(`), a wrong argument count
(`Left("abc")`), a behaviour function in a data property (`Text: =Set(...)`), a property the control lacks (`txtName.Value` on a classic
text input), an enumeration member that doesn't exist (`NotificationType.Danger`), a context variable read on another screen, or `True`
for `true`. **Fix:** `pp.py fx` and `pp.py build` now parse every formula with Microsoft's Power Fx parser and check the rest statically
([powerfx-validation.md](powerfx-validation.md) §3). Studio still binds types the checks cannot see, so the app is opened in Studio
before anyone says it works (§6). Added 2026-10-26.

---

## SharePoint lists (from the SPFx template)

Format: **symptom** → cause → guard.

| # | Trap |
|---|---|
| **T-1** | **Views and queries fail once a list passes 5,000 items** → the list view threshold. → Index every column a view or query filters or sorts by, and give the default view a filter that keeps it under 5,000. Decide the threshold strategy before the list exists. |
| **T-2** | **Random 429 / 503 under load** → throttling. SharePoint and Graph throttle independently. → Keep calls per screen few and delegable; flows use the connector's default retry policy; don't loop `Patch` over hundreds of rows from the app (use a flow). |
| **T-3** | **A column you asked to be called `ClientName` is really called `Client`, and every later write fails with "property does not exist"** → `createfieldasxml` derives the internal name from `DisplayName` unless the `AddFieldInternalNameHint` option (8) is passed. It throws nothing. → `import-lists.console.js` passes the hint and checks the returned `InternalName`. If you create fields any other way, do the same. Internal names are **permanent**. |
| **T-4** | **A column named `Type` cannot be created** → reserved. → Prefix it: `IssueType`, `LinkType`. `tools/check_schemas.py` holds the reserved list. |
| **T-5** | **`[400] -2147024809 "Value does not fall within the expected range"` on a query, naming no column** → one name in `$select` is reserved or doesn't exist. `DisplayName` is the worst case: it *creates without error*, then breaks every query that selects it. `Description` collides with SharePoint's own field. → Prefix generic names. To diagnose, remove names from `$select` one at a time until the error goes. |
| **T-8** | **"contains invalid characters" on a name with none of the listed characters** → leading/trailing spaces and trailing periods are rejected too, and the message never says so. → Trim and normalise every folder/file/list name before a create call. |
| **T-9** | **"Field 'X' cannot be referenced in filter or orderby as it is not indexed"**, even though another field in the filter is indexed → a compound filter is only as indexed as its least-indexed field. → Index **every** field a `$filter` or `orderby` touches. |
| **T-10** | **`substringof` on a multi-line text column returns a hard 400** → `Note` columns can't be filtered server-side. → Filter client-side on a bounded result, or keep a searchable Text copy. |
| **T-11** | **A Choice value works in dev and fails on the client's tenant** → the value is in code but not on the column; Choice values are a closed set fixed at creation. → Read choices from the column or a config list (dev-standards L7), and keep the schema CSV and the code in step. |
| **T-19** | **Lookup columns break when lists are provisioned to another site** → a Lookup stores the target list's GUID, which differs per site. → Store the target's item ID in an indexed Number column `<Target>Id`, plus a denormalised display value (dev-standards L3). Remap those IDs when data moves between sites. |
| **T-24** | **Item-level permissions slow to a crawl** → unique permissions on thousands of items. → Isolate with separate lists, libraries or sites instead. |

## Power Automate (from the SPFx template)

| # | Trap |
|---|---|
| **T-22** | **A flow that updates the item it triggered on runs forever** → a "created or modified" trigger fires on its own write. → Use a create-only trigger for flows that modify the triggering item. Note it polls (~1 minute) rather than firing instantly. |
| **T-25** | **A flow needs a premium licence nobody budgeted for** → `When an HTTP request is received` and the HTTP action are premium. → Trigger from a list item or a schedule; standard connectors only. |

### PA-T30 · `Navigate` in `OnVisible`

**Symptom:** a red mark on `OnVisible` with "Navigate cannot be used here since it would automatically always navigate away from this screen", even inside an `If`.
**Cause:** Studio treats `Navigate` in `OnVisible` (and `OnStart`) as a loop away from the screen being shown.
**Fix:** never navigate from `OnVisible` or `OnStart`. Show a message (a label whose `Visible` reads the condition), hide the content, or navigate from a control's `OnSelect`. A role that may not see a screen is shaped by hiding its tab and showing "You don't have access" (the lists are the access control, D6).
**Guard:** `FX-NAV`.

### PA-T31 · `IfError` with a table on one side and a boolean on the other

**Symptom:** "Invalid argument type (Boolean). Expecting a Table value instead" on the fallback of `IfError(ClearCollect(colX, ...), Notify(...))`.
**Cause:** `IfError` returns one type: the protected formula's. `ClearCollect` and `Collect` return a table, `Notify` and `Set` a boolean.
**Fix:** end the protected chain with `; true`: `IfError(ClearCollect(colX, ...); true, Notify(...))`. Chains that already end in `Notify`, `Set` or `Reset` need nothing.
**Guard:** `FX-TYPE`.

### PA-T32 · A list's data source is named after the variable's display name

**Symptom:** after adding the lists in Studio from the solution, every formula that names `PRJ_Request` is red; the data source is called `Request list`.
**Cause:** Studio names a data source that comes from an environment variable by the variable's display name, not by the list's name.
**Fix:** give every list variable the list's name as its display name (`PRJ_Request`). Flows read the same display name in their parameter (`PRJ_Request (prj_RequestList)`). A data source already added under the old name is removed in Studio and added again after the re-import.
**Guard:** `pp.py build` (the environment variable check).

### PA-T33 · Column names as text, and ErrorKind members Studio does not know

**Symptom:** "Expected identifier name" (one per text argument) and "has some invalid arguments" on `ShowColumns(List, "Title", "Value")`; "Name isn't valid. 'EditPermission' isn't recognized" on `ErrorKind.EditPermission`.
**Fix:** `ShowColumns(List, Title, Value)` with identifiers, or no `ShowColumns` at all (`ClearCollect(col, List)`). Only `ErrorKind.ReadPermission` is known to be accepted: for a refused save test the text, `"403" in FirstError.Message`.
**Guard:** `FX-ARG`, `FX-ENUM`.

### PA-T34 · A modern dropdown's `Default` is a record

**Symptom:** "Invalid formula. Expected a value compatible with 'Items'" on `Default: =varForm.Project`.
**Fix:** `Default: =LookUp(<the Items collection>, Value = varForm.Project)`. Keep the choice in a variable set by `OnChange`, so a reset is a change of the variable.
**Guard:** `FX-TYPE`.

### PA-T35 · One broken `OnStart` colours the whole app red

`App.OnStart` and the named formulas feed every screen. A single invalid argument there (a `ShowColumns` with text) leaves `colSettings` untyped, and every formula that reads a setting then shows "Incorrect format specifier", "Incompatible types" or "Invalid argument type". Read App's own errors first, fix them, and open the checker again before touching a screen. Flow calls that say "'Run' is an unknown function" mean the flows are not added to the app yet (PA-T26); `'UserProfileV2' is unknown` means the Office 365 Users data source is not named `Office365Users` (rename it in Studio).

### PA-T36 · A section with no `Height` does not fit its content

**Symptom:** a card holds a form or a table but ends part-way: the last input is missing, or only three rows of a table show. The card is as tall as a few of its rows.
**Cause:** Studio does not fit an auto-layout container to children whose heights are formulas or whose content is a gallery. The reference app's form sections happened to have fixed rows.
**Fix:** give every section an explicit `Height` that is the sum of its parts, as a formula when rows can grow: `padding 24 + heading 24 + the rows + the gaps (8 each between visible children)`. For a table: `Min(CountRows(items) * rowHeight, maximum)`. Hide the table and its header together.
**Guard:** `canvas_ui.section()` says so; check every card at the empty, one-row and many-row states.

### PA-T37 · The header title wraps

A header title at 18 pt semibold needs about 150 px for "Request Tracker" but a label sized 170 wrapped in Studio. Size title labels with at least 40 % slack for a longer client name (250), and start the tabs after it.

### PA-T38 · `Result` is not the column of a `Split` table

Studio showed `Name isn't valid. 'Result' isn't recognized` and then `The function 'Trim' has some invalid arguments` on `App.OnStart` for `LookUp(Split(text, ";"), Trim(Result) = ...)`. The column of a `Split` table is not called `Result` in Studio, and one bad name makes the whole `OnStart` red (PA-T35). Don't name the column: test a value with `in` against the table, after removing the spaces: `Lower(email) in Split(Substitute(Lower(list), " ", ""), ";")`. `pp.py fx` reports `Result` inside `Filter`, `LookUp`, `ForAll`-style calls over a `Split` as `FX-NAME`.

### PA-T39 · A badge shows a scrollbar and sits at the top of its cell

**Symptom (Studio):** a status pill (`ModernText`, 17 high) shows a small scrollbar and the text is cut; the pill is not centred in its row.
**Cause:** a `ModernText` has default padding, so a short fixed height is too small for its text. And `AlignInContainer.Start` in a horizontal container is the **top**, not the left.
**Fix:** `PaddingTop/Bottom/Left/Right: 0`, `AutoHeight: true`, `AlignInContainer: AlignInContainer.Center`. For left alignment in a column, wrap the pill in a container sized by `FillPortions`.
**Guard:** `canvas_ui.Screen.yaml()` fails a `ModernText` under 24 high without `PaddingTop: 0`; `badge_cell` in the project generator keeps columns aligned.

### PA-T40 · An SVG built by a formula draws nothing

**Symptom (Studio):** a progress bar shows its track but no fill; a ring shows no arc. No error anywhere.
**Cause:** `Text(x, "0.##")` leaves the decimal separator after a whole number (`"30."`), which is not an SVG number, so the browser ignores the shape. In a comma locale `Text(1.5)` is `"1,5"`.
**Fix:** `Substitute(Text(Round(x, 2)), ",", ".")`. Never a `Text` format for a number that goes into markup.
**Guard:** `FX-SVG` fails a formula that holds `<svg` and a `Text(…, "0.##")`; `canvas_ui.svg_bar` and `svg_ring` use the safe form.

### PA-T41 · A dialog's controls show on every screen state

**Symptom (Studio):** the form's dropdowns ("Software", "Medium", "Unassigned") float over the Overview, the ticket list and every other screen.
**Cause:** controls of a dialog are placed from its panel (`X: =pnForm.X + 20`), and each needs the **same `Visible`** as the panel. A helper that builds dropdowns had no `Visible` parameter, so those three controls were always on. Text inputs and labels had it, so the screen looked almost right.
**Fix:** `Visible` on every control placed from an overlay's panel.
**Guard:** `FX-OVERLAY` fails a control whose `X` or `Y` names a panel that has a `Visible`, when the control has none.

### PA-T42 · The Attachments table has no `Name` column

**Symptom (Studio):** "Name isn't valid. 'Name' isn't recognized" on `ForAll(LookUp(<List>, ID = x).Attachments, {Name: Name})`.
**Cause:** a SharePoint item's `Attachments` table has the columns `Id`, `DisplayName`, `Value` (the content) and `AbsoluteUri`.
**Fix:** `{Name: DisplayName}`. There is no size column: a size cannot be shown without another source.
**Guard:** `FX-NAME` on a `.Attachments` projection that reads `Name`.

### PA-T43 · Table columns do not line up and the last cell is cut off

**Symptom (Studio):** the headings are about 100 px apart whatever their `FillPortions`; in the rows every text column is about 144 px from the next, the subject is no wider than the category, and the last cell (an Edit button) is not visible. Headings and rows do not line up.
**Cause:** a Label or Classic Button in an auto-layout row has a minimum width of about 136 px, so a row of flexible cells cannot shrink to its share: it runs past the card, and the card clips what is beyond.
**Fix:** `LayoutMinWidth: 0` (and `LayoutMinHeight: 0`) on every flexible header button and every flexible row cell. `canvas_ui.table(..., fit=True)` does it for the row; the header buttons are set where they are built. Give fixed columns (pills, actions) the same fixed width in the header and in every row.

### PA-T44 · A pill in a wrapper container vanishes in a table row

**Symptom (Studio):** in a gallery row the priority and status pills are missing and every cell after them is under the wrong heading.
**Cause:** the pill (`ModernText` with a fixed width) was inside a horizontal container sized by `FillPortions`, which collapsed.
**Fix:** put the pill directly in the row, and make the pill columns fixed-width, the **same width in the header and in every row**; the other columns share the rest by `FillPortions`.

### PA-T45 · A small button shows part of its text

**Symptom (Studio):** "Previous page" and "Next page" buttons 34 px wide show "ious pag".
**Cause:** a Classic button's text is its accessible name and is drawn; it cannot be hidden or shortened.
**Fix:** the prototype's chevron as an Image (`svg_icon`) with `OnSelect`, `AccessibleLabel`, `TabIndex: 0`, `DisplayMode` and `Transparency` for the disabled state. A Classic button underneath it (text colour transparent) is the other way, when the icon needs a hover area.

### PA-T46 · Text cut off in a card, an empty state or a knowledge-base tile

**Symptom (Studio):** "Create a ticket to get started." shows its first line only; a two-line tile title is cut.
**Cause:** a label with no `Width` in a centred auto-layout column takes the width of its widest sibling and wraps; a label is one line high unless its height says otherwise.
**Fix:** a `Width` for such labels, and heights (and gallery `TemplateSize`) for the **longest** value's lines. Test with the longest sample row, not the shortest.

### PA-T47 · A comment inside a composed formula hides the rest of the line

**Symptom:** `pp.py fx` says "The formula contains 'Eof' where 'ParenClose' is expected" on a formula that looks complete in the generator.
**Cause:** a generator returned `... // AC-X.1`, and another formula appended `))` or `; Next(...)` after it: both are now part of the comment.
**Fix:** a helper that may be composed takes a `tail` and puts its comment last (`open_ticket(rec, tail)`); a nested use drops the comment.

### PA-T48 · `pp.py` rejects Studio's own `LayoutMaxHeight: =`

**Symptom:** `pp.py fx` or `build`: "not valid YAML (could not determine a constructor for the tag 'tag:yaml.org,2002:value')" on every screen that has a table wrapper.
**Cause:** an empty formula is written as a bare `=`, which PyYAML resolves to a tag it cannot construct. Studio writes it; the reference sample contains it.
**Fix and guard:** `_lint_yaml_syntax` uses a loader that constructs it as text; `test_yaml_lint_accepts_a_bare_equals`.
