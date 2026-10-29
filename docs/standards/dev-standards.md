# Development standards

How Acies builds a canvas app, its flows and its solution. The defaults (D1–D12) are in
[CLAUDE.md](../../CLAUDE.md) §4; this document is how they look in practice. Traps are cited as `PA-T…`
and `T-…` ([powerapps-traps.md](powerapps-traps.md)).

## 1. Naming

| Thing | Pattern | Example |
|---|---|---|
| Solution unique name | `PascalCase` client + project | `ContosoSiteRequests` |
| Publisher prefix | 2–8 lowercase letters/digits; the project code by default | `con` |
| List | `<LIST PREFIX>_<Entity>`, singular (L1) | `CON_SiteRequest` |
| Environment variable | `<prefix>_<PascalName>`; display name in plain words | `con_SiteRequestList` · *Site request list* |
| Connection reference | `<prefix>_<connector>`, lowercase | `con_sharepoint` |
| Canvas app | Display name in plain words; source folder `canvas/<PascalName>/` | *Site Requests* · `canvas/SiteRequests/` |
| Screen | `scr<Name>` | `scrHome`, `scrNewRequest` |
| Component | `cmp<Name>` | `cmpHeader` |
| Controls | Type prefix + purpose | `lbl` label, `btn` button, `txt` text input, `drp` dropdown, `cmb` combo box, `gal` gallery, `frm` form, `ico` icon, `img` image, `con` container, `tgl` toggle, `dte` date picker, `rec` rectangle |
| Variables | `gbl` global (`Set`), `loc` context (`UpdateContext`), `col` collection | `gblCurrentUser`, `locIsSaving`, `colDrafts` |
| Named formulas | `PascalCase` noun | `ColorPrimary`, `IsApprover`, `MyRequests` |
| Cloud flow | `<Subject> - <What it does>` | *Request - Notify approver* |
| Flow steps | Rename every step to say what it does | `Get the request`, not `Get item 2` |

## 2. Solution shape

```
solution/src/                     the solution, unpacked (SolutionPackager): the source of truth
  Other/Solution.xml              identity, version, root components
  Other/Customizations.xml        connection references (flows and apps are in their own files)
  environmentvariabledefinitions/ one folder per variable
  Workflows/                      <Name>-<GUID>.json + .json.data.xml per flow
  CanvasApps/                     <logical>.meta.xml + icon; the .msapp is built from canvas/
canvas/<App>/                     Src/*.pa.yaml (screens, App, components) + <App>.msapr
```

- **One solution, one publisher.** Everything the app needs is in it: app, flows, variables,
  references. Nothing built outside a solution.
- **Everything goes through `tools/pp.py`.** `build` packs and validates; `export` brings the Dev
  environment back into source. Never zip a folder by hand.
- A component is added to the solution once, in Dev or in source; never add Microsoft's own
  components (standard tables, system forms).

### Canvas YAML (the SourceCode layout)

Claude writes screens as `canvas/<App>/Src/scr<Name>.pa.yaml`; Studio writes the same format.

```yaml
Screens:
  scrExample:
    Properties:
      Fill: =ColorBackground
    Children:
      - conBody:
          Control: GroupContainer@1.5.0
          Variant: AutoLayout
          Properties:
            LayoutDirection: =LayoutDirection.Vertical
            LayoutGap: =Space
            Width: =Parent.Width
            Height: =Parent.Height
          Children:
            - lblTitle:
                Control: Label@2.5.1
                Properties:
                  Text: ="Requests" // AC-CON-04.1
                  Role: =TextRole.Heading1
```

| Rule | Why |
|---|---|
| Every value starts with `=` (Power Fx) | It is a formula, even a constant |
| A value containing `: ` (colon, space) is wrapped in single quotes: `Text: '="Count: " & n'`. Comments never contain `: ` | YAML reads it as a key otherwise |
| Multi-line formulas use a block scalar: `OnSelect: \|-` then the formula indented on the next lines, starting with `=` | |
| Screens are listed, in order, in `Src/_EditorState.pa.yaml` → `ScreensOrder` | Studio's navigation order |
| Gallery children sit directly under the gallery's `Children:`; the gallery carries a `Variant:` | Studio's shape |
| A control in an auto-layout container may use `FillPortions`, `AlignInContainer`, `LayoutMinWidth`, `LayoutMinHeight`, `LayoutMaxWidth`, `LayoutMaxHeight` | The container provides them |
| **Only the controls and versions below**, unless a spike proves another (CLAUDE.md §6) | `pac` doesn't check properties; Studio refuses unknown ones (PA2108, PA-T17). `pp.py build` checks these |

**Controls `pp.py` can check** (Studio 3.26091, document format 1.349):

| YAML `Control:` | Use for | Accessible name from |
|---|---|---|
| `Label@2.5.1` | Text, headings (`Role: =TextRole.Heading1…`) | Its text |
| `Classic/Button@2.2.0` | Buttons | **Its `Text`** (it has no `AccessibleLabel`; `Tooltip` adds a description) |
| `Classic/TextInput@2.3.2` | Text entry | `AccessibleLabel` |
| `Classic/Icon@2.5.0` | Icon buttons | `AccessibleLabel` |
| `Image@2.2.3` | Images | `AccessibleLabel` (blank = decorative) |
| `Rectangle@2.3.0` | Shapes, separators | `AccessibleLabel` if it is interactive |
| `GroupContainer@1.5.0` (`Variant: AutoLayout` or `ManualLayout`) | Layout | — |
| `Gallery@2.15.0` | Lists of records | `AccessibleLabel` |
| `Form@2.4.4` | Edit/view forms (data cards are added in Studio) | — |
| `Attachments@2.3.0` | List attachments | `AccessibleLabel` |
| `HtmlViewer@2.1.0` | Rich text | — |
| `ModernText@1.0.0`, `ModernButton@1.0.0`, `ModernTextInput@1.1.1`, `ModernCombobox@1.1.1`, `ModernDropdown@1.0.2`, `ModernLink@1.0.1` | Modern controls | `AccessibleLabel` |

`Text@0.0.51`, `TextInput@0.0.54`, `ComboBox@0.0.51`, `DatePicker@0.0.46` and form data cards
(`TypedDataCard`) pack, but their properties can't be checked: `build` warns, and the app must be
opened in Studio to confirm. When a project's environment runs a newer Studio, refresh
`tools/canvas-control-templates.json` from a Studio-saved app (dev-standards §12).

### Layout skeleton (proven in a Studio-built app, PA-T22)

**The safest route is to copy a Studio-built app.** When the client or the team has one (a prototype built by hand in Studio), put its unpacked source in `samples/<app>/Src/` and run a converter like `tools/examples/clone_reference_app.example.py`: it keeps every control, name, size and position, swaps colours for tokens, points the data at the project's lists and replaces the actions. Generating a layout from tokens failed three times on the first project.

A screen that Studio lays out correctly, copied from the hand-built reference app:

| Part | How |
|---|---|
| Header, navigation, tabs, current-tab underline | Labels and buttons **placed on the screen** (`X`, `Y`, `Width: =Parent.Width`), not in a container |
| Body | **One** `GroupContainer` (`Variant: AutoLayout`, vertical) at `Y: =BodyTop`, `Height: =Parent.Height - BodyTop`, `LayoutOverflowY: =LayoutOverflow.Scroll`, side padding that grows with the window up to the content width |
| Sections inside the body | Child containers with `FillPortions: =0` and an **explicit `Height`** (the sum of their rows). Rows of fields are horizontal containers with an explicit `Height` and children using `FillPortions` |
| A table | A header row (horizontal container), then a gallery inside a `ManualLayout` wrapper container whose `Height` is a number of rows (`Max(row, CountRows(items) * row)`, or a fixed maximum). The gallery uses `Variant: BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0` with only `Items`, `TemplateSize`, `Width`, `Height: =Parent.Height` and `BorderColor`; each row is one auto-layout container (`Height: =Parent.TemplateHeight`, `Width: =Parent.TemplateWidth`) and a 1 px `Rectangle` separator at `Y: =Parent.TemplateHeight - Self.Height` |
| Status badge | `ModernText` with a `Fill` from a token table, rounded with `Radius…`, the status in words |
| Dialogs | An overlay `Label` (`Visible: =varModal <> ""`), a `Rectangle` panel, and controls positioned from the panel's `X` and `Y` and shown by `varModal` |
| Choice of few values | Buttons in a row whose fill and a tick show the selection, where the prototype shows a radio group or segmented choice (a prototype `select` stays a dropdown; no checkbox control) |
| Lists of data | Loaded into **collections** on entering a screen and after each action, then filtered locally (`in` for contains); one `IfError` around the load that stores the reason for the error state |

Never set `LayoutMode` on a container or `Layout` on a gallery (PA-T21). Control versions come from Studio: `ModernDropdown@1.0.3`.

## 3. Layering (D5)

| Layer | Holds | Never |
|---|---|---|
| **Named formulas** (`App.Formulas`) | Tokens; derived values (`IsApprover = …`); reusable queries (`MyRequests = Filter(…)`) | Side effects |
| **Screens** | Layout, bindings to named formulas and data sources, the behaviour of their own controls | A business rule another screen also needs (move it to a named formula) |
| **Components** (made in Studio) or a repeated container (scaffolded) | Repeated UI (header, navigation, dialogs); content from named formulas or input properties | Data access to lists other than through properties or named formulas |
| **Flows** | Anything without the user, anything needing a connection the app shouldn't hold | Rules the user waits on that the app can do |

`App.OnStart` stays small: `Set` of a few globals at most. Prefer named formulas and `App.StartScreen`
(PA-T18).

## 4. Data rules

| # | Rule | Why |
|---|---|---|
| **L1** | Every list is named `<PREFIX>_<Entity>` (PascalCase entity, singular): `CON_QuickLink` | Identifiable among the client's own lists, and in a site's contents |
| **L2** | An item is identified by **SharePoint's own item ID**. No extra identity column | The ID is unique per list, always indexed, and costs nothing. Add a business key only where the business has one |
| **L3** | A reference to another list stores the target's item ID in an **indexed Number column named `<Target>Id`**, plus a denormalised display value (`<Target>Title`). **Never a Lookup column** | Lookups don't survive provisioning to another site (T-19) and count towards the 12-lookup limit. Item IDs change when a list is re-created: say so in `specs/data-model.md` |
| **L4** | Internal names are set explicitly, never auto-generated, and never renamed | They are permanent (T-3). Reserved or generic names collide (T-4, T-5) |
| **L5** | Every column a delegable `Filter`/`Sort`/`LookUp` uses is indexed: **every** column in a compound filter | The 5,000-item threshold (T-1, T-9) |
| **L6** | Every money column has a currency-code column beside it, unless PROJECT.md records the project as single-currency | A bare number is ambiguous |
| **L7** | Status, category and type values live on the column (Choice) or in a config list, never as literals in formulas | Adding a value must not need a release |
| **L8** | Every list has a stated **archival policy** and **threshold strategy** in `specs/data-model.md` before it goes live | Lists grow |
| **L9** | Anything a business user might change is configuration: a config list or an environment variable | Not a release (D8) |
| **L10** | Permission is enforced by list permissions, not by hiding UI | A hidden button is not access control (D6) |

## 5. Data access

- **Lists are data sources**, added in Studio from inside the solution with *automatically create
  environment variables* on (PA-T13). The data source's name is the list's name (`CON_SiteRequest`);
  formulas use that name.
- **Delegation warnings are errors** (PA-T14). Filter and sort with delegable functions (`=`, `<>`,
  `<`, `>`, `StartsWith`, `&&`, `||`, `Sort`/`SortByColumns` on indexed columns) on indexed columns.
  `Search`, `in`, `Len`, `Lower` on a column, and filters on Person or calculated columns are not
  delegable to SharePoint. `pp.py fx` and `build` check this, and the indexes, on every list in `schemas/` (`FX-DELEG`, `FX-INDEX`:
  [powerfx-validation.md](powerfx-validation.md) §3); Studio's delegation warning remains the authority.
- **Read what the screen shows.** `ShowColumns` or explicit columns where it helps; don't
  `ClearCollect` a whole list into a collection to filter it locally.
- **Writes:** `Patch`/`SubmitForm`, wrapped so failures are seen: `IfError(Patch(…), Notify(…,
  NotificationType.Error))`, or the form's `OnFailure`. A 403 means no permission: say so plainly
  (STD-PERM).
- **Who the user is:** `User().Email` / `User().FullName`. Group membership for UI shaping comes from
  the Office 365 Groups or Users connector or a config list; never a list of emails in a formula
  (PA-T6, D6).
- Text environment variables are **not** readable from a canvas app without the premium Dataverse
  connector: put such settings in a config list, or pass them through a flow.

## 6. UI

- Colours are tokens only (D11): no `RGBA(`, `ColorValue(` or hex on a screen (`/verify` check 3). Sizes are plain numbers (D11), the layout is
  [ui-patterns.md](ui-patterns.md)'s skeleton, and screens are cloned from a Studio-built reference app or built with `tools/canvas_ui.py`. Never invent a layout.
- **What** each screen holds, and how it behaves, is the accepted prototype's ([prototype-fidelity.md](prototype-fidelity.md)): its regions, controls, wording,
  flows, validations and messages. Don't redesign, simplify or omit; a platform limitation is a recorded deviation (design-spec §9).
- Every data-backed screen has the four states (design-standards §5), reachable with sample data
  during G7 so a reviewer can see them.
- Strings the user reads are in the formulas, in plain words; no codes or raw errors.

## 7. Accessibility — WCAG 2.1 AA, always

| Rule | How |
|---|---|
| Every interactive control has an accessible name | `AccessibleLabel` where the control has one (§2 table); a classic button's `Text` |
| Each screen's title is a heading | `Role: =TextRole.Heading1` on its title label; `Heading2` for sections |
| Text contrast 4.5:1 (3:1 for large text and control boundaries); focus visible | Token colours chosen for it (design-spec §8); `FocusedBorderThickness` ≥ 2 |
| Keyboard order follows reading order | `TabIndex`: `0` for interactive, `-1` for decorative |
| Images are described or marked decorative | `AccessibleLabel` with words, or blank |
| Errors and confirmations are announced | `Notify`, or a label with `Live: =Live.Polite` |
| Nothing is shown by colour alone | An icon or words with every colour state |

Run Studio's **App checker → Accessibility** before every release; fix every error.

## 8. Security

- No secrets anywhere (D7): not in formulas, variables, settings files or git.
- No people, tenant URLs, list GUIDs or site IDs in formulas or flows (PA-T5, PA-T6). `pp.py validate`
  fails them.
- Flows that run with the service account's connections don't hand their power to anyone who can call
  them: check the caller in the flow when it acts on their behalf.
- Share the app with groups, not people; the list permissions decide data access.

## 9. Traceability

Every formula implementing an acceptance criterion ends with a comment citing it, check number
included:

```yaml
Items: =SortByColumns(Filter(CON_SiteRequest, RequesterEmail = User().Email), "Created", SortOrder.Descending) // AC-CON-04.1
```

A flow step cites it in its *Notes* (`"description"` in the JSON): `"AC-CON-06.1 …"`.
`uv run tools/ac_workbook.py check <workbook> --src canvas --src solution/src` traces them. `pp.py fx` checks how they are written
(`FX-AC`): the check number present, never inside a text string, never commenting out the formula itself.

## 10. Formula conventions

- Prefer named formulas over `Set` for anything derived. Use `With()` to name intermediate values.
- Use `IfError` around anything that can fail; never `If(IsError(…))` chains.
- Comment the *why*, not the *what*.
- No dead controls, hidden "test" buttons or unused screens at release.
- Every formula is written to, and validated by, [powerfx-validation.md](powerfx-validation.md): syntax by Microsoft's parser, the
  meaning statically, then Studio and the acceptance checks. Nothing is "working" before Studio and the checks say so.

## 11. Dependencies

- Standard connectors only (D2), listed in `pp.config.json` → `allowedConnectors`. A new connector is
  a build-plan decision; a premium one is a PROJECT.md §3 override.
- No code components (PCF) or component libraries from outside the solution without a recorded
  decision.

## 12. Verification and versioning

- `uv run tools/pp.py fx` after every change to a `.pa.yaml` (formulas, properties, YAML; seconds), and `uv run tools/pp.py build`
  after every change to `canvas/` or `solution/`: 0 errors.
- When `pac` is upgraded (D12): `uv run tools/powerfx.py --refresh-functions`, then `uv run python -m unittest discover -s tools/tests`.
- `pp.py bump` before every package that leaves Dev ([alm.md](../alm.md) §2).
- **Refreshing the control set** when the client's Studio is newer: open the app in Studio, save,
  `pp.py export`; copy the app's `References/Templates.json` property lists into
  `tools/canvas-control-templates.json` (keep the shape), and update §2's table.

## 13. Deployment

[alm.md](../alm.md): unmanaged into Dev only; the same managed ZIP to Test then Prod, imported through the
portal (the importer chooses the variable values); Claude never imports into Production.
