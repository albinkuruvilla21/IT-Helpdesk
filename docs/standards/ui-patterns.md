# UI patterns: how screens are built in this boilerplate

**Read this before writing or changing any canvas screen.** It is the rule, not a suggestion.

## 1. Why this document exists

On the first project, screens were generated from design tokens, computed sizes, nested flexible auto-layout and
container badges. They built, packed and passed `pp.py build`, and then failed in Studio three times (PA2108, PA2110,
PA1001) and laid out badly (clipped text, inputs running past their section, segmented buttons cut off). The client's team
had meanwhile built the same app by hand in Studio, and **that app laid out correctly**. It is kept in
[samples/powerapp/](../../samples/powerapp/) (the `.msapp` and its unpacked `Src/`). Its patterns are encoded, number for
number, in [tools/canvas_ui.py](../../tools/canvas_ui.py), and `uv run tools/canvas_ui.py --selftest` proves the library
reproduces the sample.

**The rule: never invent a layout.** Either clone a Studio-built reference app (§2) or build every screen with
`tools/canvas_ui.py`. Do not compute sizes from tokens, do not nest flexible containers, do not draw a layout "by reasoning".
`pp.py build` checks property names; only Studio checks layout, so proven numbers are the only safeguard: the prototype's measured sizes with heights from `Design.h` (§10), or the reference numbers below.

**Whose numbers.** The numbers in §3 and §4 are the reference app's, and they are proven not to clip. When the project has an
accepted prototype, **its measured sizes, colours and chrome win** (§10, prototype-fidelity §8): the reference numbers are the
fallback for anything the prototype does not give. The structure rules (controls placed on the screen for chrome, one scrolling
body, explicit section heights, galleries in fixed wrappers) hold either way.

**What versus how.** The project's accepted prototype decides **what** is on each screen and **where**: its regions,
order, controls, wording, flows, validations and states ([prototype-fidelity.md](prototype-fidelity.md)). This document
decides **how** that is built so Studio lays it out. The reference app in `samples/powerapp/` is a source of building
techniques, not of a design: never substitute its screens, chrome or wording for the prototype's. Where the prototype
needs a pattern this library lacks (side navigation, a different header, a chart), extend the library (§9); don't
reshape the prototype to fit it.

## 2. How to start a UI

| Situation | Do |
|---|---|
| The client or team has a **Studio-built app** of the project | Put its `.msapp` in `samples/<app>/`, unpack it (`pac canvas unpack --msapp <file> --sources samples/<app>/Src --layout SourceCode`) and **clone it**: keep every control, name, size and position; change only colours (to tokens), data names and actions. `tools/examples/clone_reference_app.example.py` is the worked example for the reference app: copy it and edit its mapping |
| No reference app | Build each screen with `tools/canvas_ui.py` (§4 lists the patterns). Compose screens from its functions; never write a screen's YAML by hand |
| Either way | Run `uv run tools/canvas_ui.py --selftest`, then `uv run tools/pp.py build`, then **open the app in Studio** (§8). The person opening it pastes back what Studio says |

## 3. The skeleton (every screen)

| Part | How it is built | Numbers |
|---|---|---|
| Header band | A `Label`, `Fill: ColorSecondary`, **placed on the screen** (not in a container) | Height 56, `Width: Parent.Width` |
| Title, subtitle, user and role | Three labels on the band | Title 18 semibold at X 20 Y 6 (H 28); subtitle 11 at X 20 Y 32 (H 18); user right-aligned, `X: Parent.Width - 440`, Y 14, W 420 |
| Navigation strip | A `Label`, `Fill: ColorSurface`, on the screen | Y 56, Height 44 |
| Tabs | `Classic/Button`, transparent, on the screen | W 130, H 36, Y 60, X 20 then +136 each; the inactive tab `FontWeight.Normal` |
| Current-tab underline | A `Label`, `Fill: ColorPrimary` | H 3, W 130, Y 96, X under the tab |
| **Body** | **ONE** `GroupContainer` `Variant: AutoLayout`, vertical, scrolling | `Y: 100`, `Height: Parent.Height - 100`, `Width: Parent.Width`, gap 12, padding top 16 bottom 24, sides `Max(20, (Parent.Width - 1150) / 2)`, `LayoutOverflowY: LayoutOverflow.Scroll` |
| Sections and rows in the body | Containers with `FillPortions: 0` and an **explicit `Height`** | Never a flexible height inside the scrolling body |

Everything else goes inside the body. Nothing else is nested in an auto-layout container more than two deep.

The header, navigation and tab rows above are the reference app's chrome. Build **the prototype's** chrome (its items,
order, wording, current-item marker, and its position, scaled to the base width) with the same technique: controls placed
on the screen, not in a container. The body rules hold whatever the chrome looks like.

## 4. The patterns (all in `canvas_ui.py`)

| Pattern | Function | What it is, with the numbers |
|---|---|---|
| Screen title | `title` | 20 semibold, H 36 |
| Heading | `heading` | 15 semibold, H 26 (24 inside a section) |
| Title row with a button | `hrow` + `label` + `button` | H 40, gap 16; the label `FillPortions: 1`; the button W 190, H 36 |
| Count cards | `card_row`, `card` | Row H 70, gap 10; each card grey with a border, padding 12 / 8; caption 12 (H 20), number 24 semibold (H 34); cards share the width with `FillPortions` |
| Labelled input | `field` | A vertical column H 56: caption 11 semibold (H 18), gap 2, control H 34 |
| Row of fields | `field_row` | H 62, gap 16, three fields a row |
| Section | `section` | Grey, border, padding 12, gap 8, 15 semibold heading H 24, then rows. **Explicit Height** = rows + 12 + 24 + 8 + 12 + the gaps, as a formula when a row or table can grow (PA-T36); never auto |
| Choice of a few values | `segmented` | Buttons in a row, H 34, gap 4; the selected one filled `ColorPrimary` with `ColorOnPrimary` text. For a prototype's radio group or segmented choice; a prototype `select` stays a dropdown (`dropdown`). No checkbox control |
| Tick list | a `Classic/Button` per row reading ☑ or ☐ | W 44, H 30, size 16, with the limits as `Classic/TextInput` (H 30) in the same row |
| Read-only field | `kv` | Key 10.5 muted (H 18), value semibold (H 24), gap 2 |
| Table header | `table_header` | Grey row H 30, gap 8, padding 8, labels 11 semibold, `FillPortions` per column |
| **Table** | `table` | A header row, then a **`GroupContainer` `Variant: ManualLayout` wrapper** (`FillPortions: 0`, a fixed `Height`: `rows * template` or a maximum such as 400 to 520) holding a **gallery** (`Variant: BrowseLayout_Vertical_TwoTextOneImageVariant_ver5.0`, **only** `Items`, `TemplateSize`, `Width`, `Height: Parent.Height`, `BorderColor`). The gallery's first child is one row container (`Height: Parent.TemplateHeight`, `Width: Parent.TemplateWidth`, horizontal, gap 8, padding 8, centred) of cells with `FillPortions`; its second child is a 1 px `Rectangle` at `Y: Parent.TemplateHeight - Self.Height`. Template 46 (34 to 40 in short sub-tables) |
| Status badge | `badge` | `ModernText`, `Fill` from a `Switch` over fill tokens, radius 12, size 11 semibold, H 30 (24 in a title row), the status **in words** |
| Row action | `view_button` | H 28, `FillPortions: 0.8` |
| Filters | `dropdown` | `ModernDropdown@1.0.3` over a one-column collection `{Value}`; read with `Coalesce(<name>.Selected.Value, "All")`; search is a `Classic/TextInput` and a `... in Title` filter over the loaded collection |
| Note banner | `note_banner` | `ColorNoteFill`, border `ColorNoteBorder`, H 44, padding left 10 |
| **Dialog** | `modal_frame`, `modal_x`, `modal_y` | An overlay `Label` (`ColorOverlay`, `Visible: varModal <> ""`), a `Rectangle` panel (W 560, `X: (Parent.Width - 560) / 2`, Y 110, `Height: Switch(varModal, ...)`) and ordinary controls on the screen placed from the panel (`X: recModalPanel.X + 20`, `Y: recModalPanel.Y + n`) and shown with `Visible: varModal = "x"`. The bottom buttons sit at `recModalPanel.Y + recModalPanel.Height - 56`. Not containers |

Text sizes: body 12, captions and table headers 11, section heading 15, title 20, big number 24. Font `FontBody`.

## 5. Tokens

Every project defines the colour tokens in `canvas_ui.TOKENS` in `App.Formulas` (the client's brand replaces the values; **the names never
change**), plus the tokens its prototype needs (`ColorGlass`, `ColorSegment`, `ColorBackdrop1`... from `tools/prototype_design.py`).
`tokens_block(overrides, dark=, hexes=)` writes them: with a dark scheme each is `If(IsDark, dark, light)`, and `Hex<Name>` texts feed
SVG images. Screens use token names only: no `RGBA(`, `ColorValue(` or `#hex` on a screen (`/verify` check 3).
**Sizes are plain numbers** (CLAUDE.md D11): measured from the prototype (§10), the numbers above only where it gives none. Do not
turn them into tokens and do not compute them from a token.

Contrast: input and button outlines use `ColorBorder` (3:1 against the surface, design-spec section 8), decorative rules `ColorDivider`. Status is
always written in words as well as colour.

## 6. Data and behaviour patterns

| Pattern | Rule |
|---|---|
| Role | `OnStart` sets `varIsTreasury` (or the project's role) from a list of people (`LookUp(<ContactList>, Email = User().Email && IsActive)`). It shapes the UI only; list permissions are the access control (D6) |
| Loading | **Collections.** On entering a screen and after every action, load what the screen shows into collections (`colReqs`, `colDocs`, ...) and filter them locally. Search with `in`. Keep the collections **in the shape the screens use**: build them with `ForAll(<delegable Filter>, {Column: Source...})` so a screen reads `ThisItem.Status` (text) and not `RequestStatus.Value` |
| Reload block | One text block, repeated verbatim after every action (generate it from one variable in the generator): the collections, then `Set(varReq, LookUp(colReqs, ID = varReq.ID))` and the detail collections |
| Writes | `Patch(<List>, LookUp(<List>, ID = x), {...})`, never `Patch(<List>, ThisItem, ...)` from a collection row. A new item: `Patch(<List>, Defaults(<List>), {...})` then set its business key from the item ID. Wrap every write in `IfError` and say in words what failed |
| Actions that send email or change status | Call the project's flow (`'<Flow name>'.Run(varReq.ID, ...)`), then write the Activity row, `Refresh`, reload, `Notify` |
| Validation | As the prototype shows it: the same rules, firing at the same moment, with its message text. An inline message is a `Label` under the field (visible on the rule's condition, `Live` polite; the row's explicit height grows by 18). A toast or alert, or no visible message in the prototype, is `Notify(<what is wrong>, NotificationType.Error)` in the button's `OnSelect` |
| States | A loading label, an error label with the reason (`FirstError.Kind = ErrorKind.ReadPermission` says "You do not have access"), and an empty label. They are children of the body that take no space while hidden. `Select Dashboard to try again` re-runs `OnVisible` |
| Forms | `varForm` holds the record being edited. For a new item it is a record **with the same fields** as a row of the loaded collection (or the screens' formulas will not type-check); for an edit it is `varReq` |
| Traceability | Every formula that implements an acceptance check ends with `// AC-XXX-NN.n`. A comment on a single-quoted value goes **inside** the quotes |

## 7. What breaks Studio (each cost a round on the first project)

| Studio says | Cause | Rule (checked by `pp.py build` where marked) |
|---|---|---|
| `PA2108 Unknown property 'LayoutMode' ... 'AutoLayout'` / `'Layout' ... 'Gallery' ... 'Vertical'` | The control's template lists the property but the variant does not take it | Never set `LayoutMode` on a container or `Layout` on a gallery (checked, PA-T21) |
| `PA2110 An entity with name 'x' already exists` | Two controls on one screen share a name, usually `<prefix>Hdr` for the band and for a table header | Unique names per screen (checked, PA-T23; `canvas_ui` asserts it) |
| `PA1001 YamlInvalidSyntax ... did not find expected key` | A comment added after the closing quote of a quoted formula | Comments inside the quotes (checked, `pp.py` lint) |
| `PA2105 ... older than the current version` | A control version older than Studio's | Use the version Studio saves: `ModernDropdown@1.0.3`; refresh `tools/canvas-control-templates.json` from a Studio-saved app |
| Empty header name, empty lists, a blank button text | `OnStart` has not run in the authoring session | Not a defect: **Run OnStart** from the app's "..." menu once after opening |
| A button does nothing, no message, with a red or yellow mark on its formula | The formula names a flow that is not added to the app (PA-T26), or a column or list that is not on the site or in Studio's copy of the schema (PA-T27) | Add the flows from the imported solution; re-run the importer, **Refresh** the data source in Studio, add new lists (`pp.py build` warns about the flows and fails on names missing from `schemas/`) |
| Text clipped, inputs past their section, buttons cut off | Sizes computed from tokens, flexible heights in a scrolling body, nested containers | The skeleton in §3 and the patterns in §4 |
| Approve and Reject (or any buttons under a table) are cut off | A split row had a fixed height smaller than its card with the table at its maximum | A row that holds a table and buttons gets its `Height` from the table: `base + Min(CountRows(items) * rowHeight, maxTable)` plus any message that can appear; hide the table header with the table (PA-T22) |
| A card ends before its last field or its table rows (PA-T36) | The section had no `Height`, and Studio did not fit it to rows with formula heights or to a gallery | Every section has an explicit `Height`, a formula when rows can grow (heading + rows + gaps + padding). Never `None` |
| The header title wraps (PA-T37) | Label too narrow for the text | Title label 250 wide, tabs from X 290 |
| A screen's `OnVisible` shows `Navigate` in red | Studio refuses `Navigate` there (PA-T30) | Never navigate from `OnVisible`; show a "no access" label and hide the content |

## 8. Before you say a screen is done

1. `uv run tools/canvas_ui.py --selftest` passes (if you changed the library) and `uv run tools/pp.py build` reports 0 errors.
2. No `RGBA(`, `ColorValue(`, hex colour, `Mock`, `TODO(AC` or `HOOK` on a screen.
3. Every control name is unique; every list column a formula uses is in the schema and indexed where filtered.
4. **The app has been opened in Studio** and the errors it showed have been fixed. Until then, say "not yet opened in Studio". When Studio shows a new kind of
   error, fix the cause, add a check to `pp.py build` and a trap to `powerapps-traps.md` the same session.
5. Press every button once in Studio: each must show a message or change data. If one does nothing, read the mark on its formula (PA-T26, PA-T27).
6. At the base width and a narrow width (700) every screen has no clipped text and no control past its section.
7. **Compared with the prototype** (prototype-fidelity §7): every register row for the screen is `Built`, `Matched`, `Deviation` or
   `Out of scope`, and every deviation has its platform reason in design-spec §9.

## 9. Extending the library

A pattern the sample does not have (a chart, a calendar, a wizard) is a **spike** (CLAUDE.md §6): build it once in Studio, save, unpack
it, add its exact property set to `canvas_ui.py`, add it to `--selftest` against that unpacked source, and describe it here. Never add a
pattern from memory.

## 10. Building to the prototype's look

Measure first: `uv run tools/prototype_design.py inputs/design/<file>.html --content <content width> --out specs/prototype-design.json`
(its report lists tokens for each scheme, the type scale in points with label heights, and every radius, padding, gap and shadow,
scaled). Then build with these, passing the measured numbers in (a project generator holds them in one dictionary, read from
`specs/prototype-design.json` or copied from the report):

| Prototype draws | Use | Notes |
|---|---|---|
| Any size | `Design(scale)`: `pt(px)`, `n(px)`, `h(px, line_height)`, `w(text, px)` | Fonts in points, lengths scaled, label heights that do not clip |
| A rounded, translucent floating top bar with pill tabs | `floating_topbar(p, title, user, tabs, active, geo, logo)` | Controls placed on the screen over a `panel` (chrome is still not a container of controls). Hidden tabs take no room |
| A rounded or translucent shape behind controls | `panel(name, x, y, w, h, fill, border_color, radius, shadow)` | A ManualLayout container with no children |
| Cards and sections | `box(..., radius=, fill="ColorGlass", border=True, border_color="ColorGlassStroke", shadow="Light")`, `section(..., radius=, fill=)` | Alpha kept in the fill token: translucent over the backdrop |
| Page background, gradient, colour blobs | `Screen.backdrop = [svg_backdrop(...)]` and `Screen(..., body_fill="ColorTransparent")` | The SVG is drawn first, behind everything |
| Ring, donut, gauge | `svg_ring(name, pct, size, stroke, track, from, to, text, pt)` | Accessible name "<n> percent" |
| Logo tile, gradient shape | `svg_tile`, `svg_image` | Decorative images have an empty accessible name |
| A left side navigation with a brand, a logo tile and an icon per page | `side_nav(p, brand, items, active, geo, visible)` | Controls placed on the screen over a white `panel` with a 1 px rule; the current item filled `ColorPrimaryTint`. `visible` is a formula, so a narrow-width menu can hide it (project: `!(Parent.Width < BreakpointNarrow) || varMenuOpen`). Added on a delivered project (spike S-NAV, not yet opened in Studio) |
| Round initials badge, progress bar, line icon from the prototype's SVG | `avatar`, `svg_bar`, `svg_icon` | `avatar` is a `ModernText` with radius size/2; the other two are Images of an SVG whose colours are `Hex<Token>` texts |
| Table rows on a white card instead of the page colour | `table(..., row_fill="ColorSurface", row_pad=17, row_gap=10)` | Defaults keep the reference app's numbers |
| Pill or rounded buttons, badges | `button(..., radius="pill")`, `badge(..., radius=, size=)` | |
| Light and dark | `tokens_block(dark=..., hexes=...)`; `App.OnStart`: `ClearCollect(colScheme, {Value: <the ColorScheme setting, default the prototype's>})` | The device setting cannot be read: record that one deviation |

**Proof.** Every property these patterns set is in Studio's control templates and every formula they write passes Microsoft's Power Fx
parser (`tools/tests/test_prototype_fidelity.py`). They have **not yet been opened in Studio**: the first project that uses them lists
**S-UI** in build-plan §7 (SVG images render, translucent fills and radii show, `IsDark` switches every colour), proves it, then adds
the Studio-saved result to `canvas_ui.py --selftest` (§9). Until then a pattern that misbehaves is fixed in the library, not avoided.
