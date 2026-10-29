# Inputs summary: Acies Innovations IT Help

Written by `/ingest` on 2026-10-29. Two inputs: the BRD and the HTML prototype. No transcript, no brand guide.

## 1. BRD: `brd/Helpdesk_BRD.xlsx`

| Item | Finding |
|---|---|
| Sheets | `Helpdesk_BRD 1.0` (21 numbered feature rows, R2 to R22 of the converted file, plus effort, rate, cost and payment notes) and `Timelines` (8-week indicative plan) |
| Requirements sheet | `Helpdesk_BRD 1.0`: columns Sr No, Module, Feature, Sub-Feature, Description, Out of Scope & Assumptions, Comments, Queries, License Cost. Cite as `BRD: Helpdesk_BRD 1.0!R<row>` |
| Reference sheet | `Timelines` has no requirements. Estimate: 140 hours, INR 2,150 per hour, INR 301,000 excl GST (commercial, not scope) |
| Damage | None seen: no merged-cell loss, no empty sheet. Sr No 22 and 26 are skipped in the source (numbering gap only) |
| Secrets | None. No password, token, key or login in either input. `git ls-files inputs` lists only the README and `.gitkeep` files, so nothing is in history yet |

Feature rows (Sr No): 1 Solution Architecture · 2 Navigation & Header · 3 Overview Dashboard · 4 Ticket List, Search & Filters · 5 Create Ticket Form · 6 Ticket Validation · 7 Ticket Attachments · 8 Ticket Detail View · 9 Update Status, Priority & Assignment · 10 Edit Ticket Details · 11 Comments & Activity Timeline · 12 Resolve & Close Ticket · 13 Delete Ticket · 14 My Tickets & Assigned to Me · 15 Ticket Assignment · 16 Outlook Notifications · 17 Knowledge Base · 18 Categories, Priorities, Statuses & Technicians (master data) · 19 Role-based Access · 20 CSV Export.

Out of scope per BRD (Sr No 1): SLA timers, escalation, ITSM integration, Teams or SMS, asset/change/problem management, Power BI, mobile-specific layout and dark theme.

### BRD against prototype: differences

| Topic | BRD | Prototype | Handling |
|---|---|---|---|
| Dark theme, mobile layout | Out of scope | Dark toggle and breakpoints built | Q-04 |
| Roles | Requester, Technician, Administrator | One fixed technician user who can do everything | Q-03 |
| Delete | Administrators only | Any user | BRD wins (D6); Q-11 |
| Requesters see only their own tickets | Yes (R4, R8) | All tickets visible | BRD wins; list permissions (D6) |
| Outlook notifications | Five events | In-app bell only | AC from the BRD; no prototype view |
| CSV export | Yes | Absent | AC from the BRD; Q-17 |
| Approvals menu | Asked about | Absent | Q-12 |
| Master data in SharePoint lists | Yes | Hard-coded arrays | Lists in G5 |
| Settings | Read-only reference | Also holds a demo "Reset" card | Q-05 |

## 2. Prototype: `design/index (4).html`

One self-contained file (inline CSS and script, Inter loaded from Google Fonts; no other files). Read in full, source not only the conversion. No browser tool was used, so no screenshots: the register comes from the source.

| Item | Finding |
|---|---|
| Views | Overview, All tickets, My tickets, Assigned to me, Knowledge base (list and article), Settings; overlays: create/edit modal, ticket drawer, confirmation dialog, notifications and profile dropdowns, toasts, loading state |
| Register | `specs/prototype-fidelity.md`: 13 views and overlays (8 views, 5 overlays), **117 rows** by kind: action 21, list 15, state 14, layout 13, style 13, content 11, control 10, derived 6, responsive 5, validation 5, navigation 2, conditional 1, role 1 |
| Accepted? | Nothing says which version the client accepted or when: Q-01 |
| Scripted behaviour | All in the `<script>`: filter/sort/paging, create/edit validation, status/priority/assignee changes with activity logging, comments, confirmations, theme toggle, knowledge base search and chips |
| Gaps in the prototype | No hover-only content, no drag-and-drop, no date inputs. File input needs `Attachments` (spike). Charts are CSS bars (build as Images from SVG or sized labels) |
| Platform limits seen | None blocking. Collapsible sidebar and slide-in drawer need container or visibility tricks (BRD R3 already says "subject to control support") |

### Mock data: the first draft of the data model

| Entity | Fields |
|---|---|
| Ticket | `id` (HD-nnnn), `subject`, `description`, `requesterName`, `requesterEmail`, `category`, `priority`, `status`, `assignedTo` (name), `createdAt`, `updatedAt`, `attachments[]` (`name`, `size`), `comments[]` (`a` author, `at`, `x` text), `activity[]` (`at`, `text`) |
| Knowledge article | `c` category, `t` title, `d` description, `s[]` steps |
| Lookups | Technicians (4), Categories (Hardware, Software, Network, Access, Other), Priorities (Low, Medium, High, Critical, each with a definition), Statuses (Open, In Progress, On Hold, Resolved, Closed, each with a definition) |

So: lists for Tickets, Comments, Activity, Knowledge articles, Technicians, Categories, Priorities, Statuses (G5 decides). Ticket attachments use SharePoint list attachments.

### The look

Output of `tools/prototype_design.py`, kept in `specs/prototype-design.json`. Scale 1.5 (content 1020 / 680).

| Item | Finding |
|---|---|
| Schemes | Light and dark. The tool reported "dark scheme: False" because the prototype switches by `data-theme="dark"` on `<html>`, not by the media query; the dark values were read by hand into register rows P-131 and P-132 |
| Accent | Indigo `#4f46e5` (light), `#818cf8` text/accent in dark, primary button `#4f46e5` in both |
| Page, card, text | Light `#f6f7f9` / `#ffffff` / `#101828`; dark `#0b0f17` / `#121826` / `#e6e9ef` |
| Fonts | Inter 400/500/600. Tool matched `Segoe UI`; Inter is not a Studio font (Q-02) |
| Type scale | Body 14 px (16 pt), h1 18 px (20 pt), stat 26 px (29 pt), table head 12.5 px (14 pt), small 12 px (13.5 pt) |
| Radii | 8 / 10 / 12 px (12 / 15 / 18 scaled), pill 12 px (18) |
| Shadows | Dropdowns, modal and toast only |
| Background | Flat colour, no gradient, no image, no blur |
| Failing contrast pairs | The tool listed none. It did not test the by-hand dark values, nor the 14 % tinted badge fills; `/design-spec` must check those (muted `#667085` on `#f6f7f9` is about 4.6:1, close to the 4.5:1 limit) |

## 3. Brand guidelines

None in `inputs/branding/`. The design carries usable colours in both schemes, so the brand is **derived from the prototype, no brand guide** (D11). Q-02 asks the client to confirm.

## 4. Studio-built reference app

`samples/powerapp/` holds one (`...-document.msapp` with `Src/`). Screens will be cloned from or built with its patterns (`ui-patterns.md`). No Studio-built version of this project's own main screen exists yet.

## 5. Reuse candidates

`uv run tools/catalogue.py fetch` at project set-up returned **0 entries** (catalogue at `3502b2e`), so there is nothing to suggest. PROJECT.md §8 is unchanged. `/build-plan` checks again.

## 6. Gaps

| Gap | Effect | Later stages will |
|---|---|---|
| No transcript | No PO decisions recorded | Ask through the 17 open questions in PROJECT.md §4 |
| No brand guide | Brand taken from the prototype | Record "derived from the prototype, no brand guide" in design-spec; Q-02 |
| Acceptance of the prototype not recorded | Q-01 | Use the file as it is |
| Roles and groups unknown | Permission design blocked on names | Design three roles on list permissions (D6) with placeholder groups |
| Tenant facts, environments, people (PROJECT.md §1, §5, §6.1) | Still 🔶 from G0 | Stay 🔶 until the client answers |
| No screenshots of the prototype | Visual comparison at G7 has no baseline | `visual_compare.py` measures the HTML in Chromium directly |
| Prototype has no notification email, CSV export, role differences | Drafted from the BRD only | `/acceptance-criteria` marks the source as BRD |

## 7. Next step

`/acceptance-criteria` (G2). The Client PO signs the workbook off; nothing after it starts before then.
