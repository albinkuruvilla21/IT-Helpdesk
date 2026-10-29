# Prototype fidelity

**The accepted prototype is the specification for what the user sees and does.** The job is to translate it
into a working Power Apps solution, not to design a new one. This document says how to read a prototype, how
its parts become native canvas controls, what counts as a reason to differ, and how the result is checked
against it. CLAUDE.md §7 is the summary.

## 1. The rule

1. **Inspect the prototype thoroughly before building** (§3). Every view, control, validation, message,
   action and state goes in the fidelity register (§4) before anyone builds from it.
2. **Replicate it** (§5): appearance, layout, user flows, validations and behaviour, as closely as native
   Power Apps controls and this template's architecture allow. Wording verbatim. Region order, hierarchy,
   grouping and proportions kept.
3. **Do not redesign, simplify or omit** anything it demonstrates, unless the client has decided otherwise
   (an AC row, a recorded PO decision) or a platform limitation forces it (§6). Then record the deviation and
   build the closest equivalent that keeps the behaviour.
4. **Validate the result against it** (§7) and fix every discrepancy that isn't a recorded deviation.

## 2. How it fits with the other rules

| Rule | How the prototype fits |
|---|---|
| **The approved AC are the scope** (CLAUDE.md §3 rule 6) | The AC is drafted from the prototype (G2), so every behaviour it shows has a criterion. After sign-off the prototype fills in the detail a criterion doesn't spell out (layout, wording, order, messages, the steps of an interaction): building that detail is **not** scope creep. A row the PO set `Out of Scope` or `Won't` is not built, and the register says so. A whole feature the prototype shows with **no** AC row at all is neither built quietly nor dropped quietly: it goes in a proposed change (`/acceptance-criteria` §6) and on the report |
| **Never invent a layout** (`ui-patterns.md`) | The prototype decides **what** is on each screen and **where**. `ui-patterns.md` and `tools/canvas_ui.py` decide **how** it is built so Studio lays it out (controls placed on the screen, one scrolling body, explicit heights, galleries in wrappers). Neither replaces the other: the reference app's layout is never substituted for the prototype's |
| **Tokens only** (D11) | The prototype's colours **in each scheme it defines**, measured by `tools/prototype_design.py`, become tokens (`/design-spec`); screens use the names. With no brand guide they are the brand |
| **Sizes are plain numbers** (D11) | Every size is **measured from the prototype** and scaled to the app (§8): font sizes, label heights from the CSS line-height, radii, paddings, gaps, card and control heights, positions and proportions. `ui-patterns.md`'s reference numbers are used only where the prototype gives none. Never compute a size from a token |
| **Checked controls only** (dev-standards §2) | Every prototype control becomes a native control from the checked list (§5). One with no checked equivalent is a spike, not a reason to drop it |
| **Accessibility** (D9) and the **Acies defaults** (D1–D12) | They override the prototype. The compliant variant is a recorded deviation (design-spec §8, §9) |
| **Scope discipline** (CLAUDE.md §8) | "The thinnest thing" means nothing beyond what the prototype and the AC show. It never means less than the prototype shows |

## 3. Inspect before building (G1, again at G7 per screen)

**Read the source, not only the conversion.** An HTML prototype's behaviour lives in its scripts and
attributes; the converted copy in `inputs/_converted/design/` keeps them (with embedded images stubbed), but
nothing runs. Read the original `.html` and any CSS and JS beside it. If a browser tool is available, open
it and screenshot every view and state into the scratchpad; otherwise rely on the PNGs.

Enumerate, into the register:

| Look for | Where it hides | Record |
|---|---|---|
| Every view, including the ones a click reveals | Sections toggled by script (`display`, `hidden`, `classList`), tabs, hash routes, modals and drawers in the markup but hidden | One screen or dialog each; how it is reached |
| Every region, in order | Landmarks, headings, `section`/`div` structure, grid and flex CSS | Order, hierarchy, grouping, alignment, proportions |
| Every control | `input` (by `type`), `select`, `textarea`, `button`, links acting as buttons, clickable `div`s | Type, label, placeholder, default value, options **in their order**, enabled/disabled |
| Every validation | `required`, `pattern`, `min`/`max`, `minlength`/`maxlength`, `type=email`, script checks, cross-field rules | The rule, when it fires (typing, leaving the field, submit), and **the exact message text** and where it shows |
| Every action | Event handlers (`onclick`, `addEventListener`, `submit`) | What it changes, where it navigates, any confirmation, the message shown after (toast, banner, inline) |
| Conditional display | Script that shows, hides, enables or disables | The condition, in plain words |
| Lists and tables | Table markup, script that renders rows | Columns and their order, sort order, filters, search, paging, row actions, counts, the empty message |
| Derived values | Script arithmetic, date formatting, status logic | The formula in plain words, its format (dates, numbers, currency) |
| States | CSS classes such as `.empty`, `.error`, `.loading`, `.selected`, `.active`; disabled styles | Each state each screen shows |
| Roles | Script branches on a user or role | What differs, per role |
| Mock data | Arrays and objects in the script | Fields, types and sample values: the first draft of the data model |
| Responsive behaviour | `@media` rules, flex wrapping | Breakpoints and what moves |
| **The look** | `:root` custom properties, `@media (prefers-color-scheme: dark)`, `font`, `border-radius`, `box-shadow`, `backdrop-filter`, gradients, `::before` decorations | Run `uv run tools/prototype_design.py <file>.html --content <app content width> --out specs/prototype-design.json` and keep its report. One register row (kind `style`) for each: the colour schemes, the page background, the chrome, the card style, the button styles, the badge style, the type scale, the field style, decorations (a logo tile, a ring) |
| Content | Every heading, label, button text, help text, tooltip | Verbatim |

**Figma?** Read it through `tools/figma_pull.py` (inputs/README.md *The design*): the frames' PNGs are the views, and
`values.md` the measured values. **Never** inventory an HTML that was converted from a PDF or images: it is not the design.

**PNG or PDF only?** `ingest.py` reports a *prototype gap*: the look can't be measured, so ask for the Figma file or the
real HTML (PROJECT.md §4). Meanwhile, the same inventory from the images (look at every one). Behaviour no image shows is an
open question with a baseline, not a guess.

## 4. The fidelity register

`specs/prototype-fidelity.md`, from [the template](../templates/prototype-fidelity.template.md): one row per
element or behaviour (`P-nn`). It is how anyone checks that nothing was redesigned, simplified or dropped.

| Column | Filled by |
|---|---|
| P-ID, screen, element or behaviour, kind, prototype reference | `/ingest` (G1) |
| AC IDs | `/acceptance-criteria` (G2). Every row gets an AC ID, or a note why not |
| Built as (screen and control, named formula, flow) | `/ui-dev` (G7), `/functionality-dev` (G8) |
| Status | G7, G8, G11 (below) |

| Status | Means |
|---|---|
| `Not built` | Inventoried, not yet implemented |
| `Built` | Implemented and compared with the prototype **in source**; not yet compared in Studio |
| `Matched` | Compared with a Studio screenshot of the built screen and it matches: by eye side by side, or with `tools/visual_compare.py run` (screenshots in `specs/screenshots/`; it says `matches` or `accepted`, and the comparison image was looked at). The tool is optional |
| `Deviation` | Differs for a reason §6 allows; design-spec §9 has the row |
| `Out of scope` | The PO excluded it: the AC row that says so |

A new or changed prototype after G1: re-inventory the changed views (`/status` reopens the stages).

## 5. Translating to native controls

Build each with the `canvas_ui.py` pattern named (`ui-patterns.md` §4). Keep the prototype's control type
where a native one exists; don't swap a dropdown for buttons, or a table for cards, because one is easier.

| Prototype | Power Apps | Pattern / note |
|---|---|---|
| A page or view | Screen `scr<Name>` | `Screen`, `chrome` |
| Header, top navigation, tabs | Labels and buttons placed on the screen, over a `panel` when the prototype's bar is rounded or translucent | `floating_topbar` (a rounded bar, segmented pill tabs, logo tile), or `topbar` / `chrome` for a flat band. Take the prototype's items, order, wording, current-item marker, sizes and colours |
| Side navigation, or a header neither pattern matches | Labels and buttons placed on the screen, over `panel`s | Compose from `panel`, `button(radius=...)`, `label`; add it to the library (ui-patterns §9) |
| Card, panel, glass surface | An auto-layout container with the prototype's fill (alpha kept: translucent), border, radius and shadow | `box(..., radius=, fill=, border_color=, shadow=)`, `section(..., radius=, fill=)` |
| Page background: a colour, a gradient, colour blobs | The screen's fill plus an Image showing an SVG drawn from Hex tokens, behind a transparent body | `svg_backdrop` in `Screen.backdrop`, `body_fill="ColorTransparent"` |
| Ring, donut, progress arc, gauge | An Image showing an SVG built by a formula | `svg_ring` |
| Logo tile, gradient shape, decorative icon | An Image showing an SVG | `svg_tile`, `svg_image` |
| Pill or rounded button | `Classic/Button` with the prototype's radius | `button(..., radius="pill")` |
| Light and dark schemes | Every colour token `If(IsDark, dark, light)`; `IsDark` from `colScheme`, set from configuration | `tokens_block(dark=..., hexes=...)`; design-standards §3 |
| Text input, textarea | `Classic/TextInput` (`Mode: TextMode.MultiLine` for a textarea) | `field` |
| `select` | `ModernDropdown` over a one-column collection, the options in the prototype's order | `dropdown` |
| Radio group, segmented choice | Buttons in a row, the selected one filled | `segmented` |
| Checkbox, toggle | A `Classic/Button` reading ☑ or ☐ | Tick list (ui-patterns §4) |
| Date input | `DatePicker` (packs, not checkable: confirm in Studio, PA-T17) | Spike (CLAUDE.md §6) |
| File input | `Attachments` in a form | Spike |
| Table, list of records | A gallery in a fixed-height wrapper, the prototype's columns in its order | `table_header`, `table` |
| Status pill or badge | `ModernText`, the status in words | `badge` |
| Summary cards, counters | Card row | `card_row`, `card` |
| Modal, drawer, confirmation | Overlay, panel and controls placed from it, shown by `varModal` | `modal_frame` |
| Toast, alert after an action | `Notify` with the prototype's text and type | |
| Inline validation message | A `Label` under the field, visible on the rule's condition, `Live` polite; the field row's explicit height grows by the label's (H 18 at size 11) | When the prototype shows inline messages. `Notify` only where the prototype uses a toast or alert |
| Banner, note | Note banner | `note_banner` |
| Icon | `Classic/Icon`, the closest built-in icon, with an accessible name | Client SVG as media if no built-in icon is close |
| Bar or line chart | An Image showing an SVG built from the data (like `svg_ring`) | Spike: add the pattern to the library (ui-patterns §9) |
| Calendar, wizard | Not in the library | Spike (ui-patterns §9) |
| Hover-only content or menu | Shown on select or focus as well | Deviation (hover isn't reachable by keyboard or touch) |
| Drag-and-drop | Move-up / move-down buttons | Deviation |

## 6. Platform limitations: what counts

| A reason to differ | Not a reason |
|---|---|
| The control or behaviour doesn't exist in canvas apps (true hover, drag-and-drop between lists, `backdrop-filter` blur, following the device's light/dark setting by itself) | It is simpler or faster to build another way |
| No checked control does it and the spike failed (or is still pending: build the closest checked control meanwhile) | `canvas_ui.py` has no pattern for it (extend the library, ui-patterns §9) |
| As drawn it fails WCAG 2.1 AA | The Studio-built reference app does it differently |
| It would break an Acies default (D1–D12) that PROJECT.md §3 doesn't override | It "looks close enough" |
| Delegation or connector limits at the list's volume | The AC doesn't mention that detail |
| The font isn't one Power Apps offers | It didn't fit the time |
| | The reference app's chrome, sizes, square cards or flat colours differ from the prototype |
| | Rounded corners, shadows, translucency, a gradient background, a ring or a second colour scheme "aren't native": they are (§8) |

Every deviation: a design-spec §9 row (*design shows*, *built as*, *why*: the platform reason), the register
status `Deviation`, and the closest equivalent that keeps the behaviour. The design lead tells the client.

## 7. Validate against the prototype

| When | What |
|---|---|
| **G7, each screen** (mock data) | Read the screen's prototype source and images again. Compare region by region: order, every control present, control type, labels verbatim, alignment and proportions, colours through tokens, every state. Walk every interaction in the register: each click, each validation with bad input and its message, each navigation, each show/hide. Fix each difference, or record it as a deviation. Status → `Built` |
| **G8, each behaviour** | Validations, messages, derived values, sort orders and conditional rules against the real lists, compared with what the prototype's script does |
| **In Studio** (a person; `visual_compare.py` optional) | Screenshot each screen's canvas in every state and scheme. Compare side by side with the prototype's view, or put the screenshots in `specs/screenshots/` and run `uv run tools/visual_compare.py run` and look at each comparison image. Rows that match → `Matched`. Differences come back as fixes or recorded deviations |
| **G11** (`/verify` check 17) | No row `Not built`. `Built` rows are reported as "not yet compared in Studio" |

A discrepancy found at any stage is fixed at its cause (the screen, the pattern, or the library) and
compared again; it is never closed by editing the register.

## 8. Visual fidelity: the look, measured

Structure and behaviour are not enough: an app with the right regions in the reference app's sizes and colours does not match the
prototype. The look is measured, not judged by eye.

| Step | How | Where it lands |
|---|---|---|
| 1. Measure (G1, G3) | As rendered: `uv run tools/visual_compare.py measure <screen>` (Chromium: the cascade, inherited type, script-drawn views, each scheme, a frozen clock). From the CSS: `uv run tools/prototype_design.py inputs/design/<file>.html --content <app content width> --out specs/prototype-design.json`. It reads every `<style>`: custom properties of `:root` and of `@media (prefers-color-scheme: dark)`, every font size, radius, padding, gap, height, shadow, gradient and font stack | The register (`style` rows), SUMMARY.md |
| 2. Colours, both schemes (G3) | Its token proposal: each custom property mapped to a token name, the light and the dark value, contrast of every text token on its surface, and the nearest compliant shade where a pair fails (D9 wins; design-spec §8). With no brand guide this is the brand | `App.Formulas` through `canvas_ui.tokens_block(overrides, dark=, hexes=)`; design-spec §2 |
| 3. Scheme | Each colour token is `If(IsDark, <dark>, <light>)`. A canvas app cannot read the device's light/dark setting, so `IsDark` comes from `colScheme`, loaded in `App.OnStart` from configuration (a `ColorScheme` setting, default the prototype's default scheme). That is the one recorded deviation; a scheme switch is added only if the prototype or the AC has one | design-spec §2, §9 |
| 4. Type scale (G3) | Points = px × scale × 0.75, where scale = app content width / prototype content width (the tool prints both). Label height = points ÷ 0.75 × line-height (`Design.h`) | design-spec §3; the generator's `Design` |
| 5. Geometry (G3, G7) | Radii, paddings, gaps, card min-heights, control heights, positions: the tool's scaled values. A `999px` radius is `"pill"` (half the height) | design-spec §4; the generator |
| 6. Surfaces and decoration (G7) | Translucent fills keep their alpha (`ColorGlass`); borders keep their colour (`ColorGlassStroke`); shadows map to `DropShadow` (Light for soft card shadows); gradients and colour blobs are `svg_backdrop`; rings `svg_ring`; logo tiles `svg_tile`. Colours inside an SVG come from `Hex<Token>` named formulas, never literals | The screens |
| 7. Compare (G7, Studio) | `uv run tools/visual_compare.py run` against the Studio screenshots, then by eye on each comparison image. Beside the prototype, in **each scheme**, at the base and narrow widths: colours, type sizes and weights, radii, spacing, shadows, background, chrome, badges, buttons, fields. `uv run tools/prototype_design.py ... --check canvas/<App>/Src/App.pa.yaml` (`/verify` check 20) fails a measured colour with no token, or a dark prototype with no `IsDark` | Register rows `Matched`, or `Deviation` with a §6 reason |

What still cannot match, and is recorded once as a deviation: backdrop **blur** (the translucent fill stays, the blur does not),
the scheme following the **device setting** automatically, and fonts Power Apps does not offer. Everything else in this section is
built.

The patterns in step 6 use only verified controls and properties (`pp.py build` checks them; `tools/tests/test_prototype_fidelity.py`
proves it), but have not yet been opened in Studio: until a project proves them, list them as spike **S-UI** in build-plan §7
(ui-patterns §10).
