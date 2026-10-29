# Acies Innovations IT Help — release 1.0.2.0

> Written by `/verify release` for the delivery lead (stage **G11**). Also the hand-over note for whoever
> imports it.

| | |
|---|---|
| Packages | `releases/AciesInnovationsITHelp_1_0_2_0_managed.zip` · `releases/AciesInnovationsITHelp_1_0_2_0.zip` (unmanaged, Dev only) |
| Version | 1.0.2.0 |
| Built | 2026-10-29, from commit 35e36a5 plus the G11 changes |
| `pp.py build` (validation) | ✅ 0 errors · 105 warnings: 1 YAML-packed app (PA-T8), 104 `FX-DELEG` suppressions listed under *Known issues* |
| `check_schemas.py` | ✅ 9 schemas, 0 errors |
| `ac_workbook.py check --src canvas --src solution/src` | 43 live criteria, 41 traced to the app or flows (AC-ITH-10 and AC-ITH-30 are deliberately not built), 42 with tests (AC-ITH-30 has none) |
| Solution checker (`pp.py check`) | not run: needs pac auth against a tenant |
| Tests (latest iteration) | 0 pass · 0 fail · 0 blocked · 185 not run (none executed yet) |

**Formula validation, by level** (`docs/standards/powerfx-validation.md` §1)

| Level | Result |
|---|---|
| 1–2 Static | Syntax confirmed by Microsoft's Power Fx parser 1.99.0.0: 10,649 formulas, all confirmed. Static checks 0 errors. 413 list queries and 72 writes checked against `schemas/`; 339 names in the record scope of an unknown table are not checked |
| 3 Studio App checker | **Opened by the delivery team on 1.0.1.0; one formula error found and fixed (PA-T42); App checker → Formulas not yet reported clean for 1.0.2.0** |
| 4 Acceptance checks walked | Not done |

## What's in it

| Piece | Kind | AC IDs |
|---|---|---|
| `IT Help` (`ith_ithelp_572fd`): scrOverview, scrTickets, scrKnowledge, scrSettings, with the sidebar, header, create/edit form, ticket panel and close dialog on every screen | Canvas app | AC-ITH-01 to 09, 11 to 29, 31, 35 to 43 |
| Notify requester - ticket created | Flow | AC-ITH-32 |
| Notify technician - ticket assigned | Flow | AC-ITH-33 |
| Notify requester - ticket updated | Flow | AC-ITH-34 |
| `ITH_Ticket`, `ITH_TicketComment`, `ITH_TicketActivity`, `ITH_Article`, `ITH_Technician`, `ITH_Category`, `ITH_Priority`, `ITH_Status`, `ITH_UserRole` | SharePoint lists (`schemas/`, created by hand on the site) | all data criteria |
| 13 environment variables: the site, 9 list variables, `ith_NotificationMailbox`, `ith_AppLink`, `ith_MailOverride` | Solution | AC-ITH-32 to 34 |
| 2 connection references: `ith_sharepoint`, `ith_office365outlook` | Solution | AC-ITH-32 to 34 |

Not built, by PO decision: ticket delete (Q-11, AC-ITH-30), phone layout (Q-04, AC-ITH-10), demo features (Q-05, AC-ITH-44), an Approvals menu (Q-12). Proposed changes to the criteria: `specs/acceptance-criteria/proposed-changes-2026-10-29.md`.

## Changes since the last release

1.0.2.0 fixes what the first Studio pass found (video `uiglitch/`, 2026-10-29):

| Fixed | Cause (trap) |
|---|---|
| The form's category, priority and assignee dropdowns showed on every screen | No `Visible` on the overlay's dropdowns (PA-T41) |
| Ticket table: priority and status pills missing, headings off the card and under the wrong columns | Pills in wrapper containers, header buttons with a minimum width (PA-T43, PA-T44): the Priority, Status and Actions columns are now fixed-width in the header and every row |
| Pager showed "ious pag" | Replaced by chevron icons with names (PA-T45) |
| Status bars had no fill | `Text(x, "0.##")` in the SVG (PA-T40) |
| "Create a ticket to get started." and the knowledge-base tile titles cut off; the priority legend clipped | Label widths and heights (PA-T46); the Overview row is taller |
| `Name isn't valid` when opening a ticket | The Attachments table's column is `DisplayName` (PA-T42) |

The first candidate, 1.0.1.0, is still in `releases/` and is superseded.

## Known issues

| Item | Detail |
|---|---|
| Opened in Studio once, not signed off | The delivery team opened 1.0.1.0 in Studio and reported the glitches fixed above; 1.0.2.0 has not been opened yet. The layout of every screen (sidebar, header, panel, overlays), the SVG icons and badges, the `IsDark` switch, and the gallery `WrapCount` and `OnSelect` are checked statically only (S-UI, S-NAV, S-DRAW, build-plan §7). Expect a round of fixes |
| Attachments (S-ATT, AC-ITH-23) | The create form has **no file field**: SharePoint attachments need an `Attachments` control inside a Form data card, which cannot be generated. The panel lists attachments an item already has, by name only (SharePoint returns no size, DEV-05). Outstanding for Studio |
| CSV export (S-CSV, AC-ITH-42) | Uses `Download()` with a data URI; unproven. If Studio or the browser refuses, a flow must produce the file |
| Dark/light choice | Not remembered between sessions (DEV-02, Q-22) |
| `?ticket=<id>` link | The emails link to the app with `?ticket=<id>`; the app opens that ticket on start. Unproven; needs `ith_AppLink` to be the app's play URL |
| Flow operations | `GetOnNewItems`, `GetItem` and `SendEmailV2` (with `emailMessage/From`) were written without a tenant: open each flow in the designer after import and confirm the operations and the shared-mailbox "Send as" |
| Data row limit | Set **Settings → Data row limit to 2,000** in Studio (the app reads up to 2,000 tickets; Q-07 baseline "under 2,000") |
| Roles | Roles come from `ITH_UserRole` (D-03). SharePoint list permissions still need the client's groups (IN-01); until then everyone who can open the lists can read them (Q-23, Q-24) |
| Sample data | Schemas carry example.com sample rows; replace the articles, categories, priorities and technicians with the client's (IN-02, IN-03) |
| Suppressed warnings | 104 `FX-DELEG` suppressions, three reasons: (1) ticket and activity reads capped by the 2,000 data row limit, by design, baseline Q-07 (agreed by Albin 2026-10-29); (2) one ticket's comments and activity, far under the limit; (3) role and master-data lists under 500 items, by design (`specs/data-model.md`) |
| Open questions | Q-01 to Q-24 in PROJECT.md §4; those not answered use their baselines |
| Tests | 185 tests, none run. Flow tests are blocked until IN-04 (the sending mailbox) and the connections exist |

## Deviations from the prototype

14 register rows are `Deviation`, 8 `Out of scope`, 94 `Built` (not yet compared in Studio). Each deviation and its reason (`specs/design-spec.md` §9):

| ID | Deviation | Reason |
|---|---|---|
| DEV-01 | Segoe UI instead of Inter; two font weights | Inter is not offered |
| DEV-02 | Starts in the light scheme; the toggle is not remembered | The device setting cannot be read |
| DEV-03 | No Escape key, no slide-in, no animation | Platform |
| DEV-04 | `Notify` messages instead of toasts | Platform |
| DEV-05 | Real attachments (outstanding), names only, no help text | AC-ITH-23 and SharePoint |
| DEV-06 | No delete | PO decision Q-11 |
| DEV-07 | One 1366 px layout | PO decision Q-04 |
| DEV-08 | No demo features | PO decision Q-05 |
| DEV-09 | Long text cut in the formula | A label cannot ellipsise |
| DEV-10 | Weight 500 shown as Normal or Semibold | Two weights |
| DEV-11 | Hover fills where the control supports them | Platform |
| DEV-12 | Sidebar width switches without animation | Platform |
| DEV-13 | No dot in the badges | A text control cannot hold a shape |
| DEV-14 | Text-only buttons (no plus or pencil icons) | A Classic button holds no icon |

Accessibility resolutions (§8): control outlines `#838a98`/`#657084` (3:1), darker text for four light badges, a legend and text alternative for the priority bar, and `ColorPrimary` kept `#4f46e5` in dark.

## Deploying

1. **Lists** on the site: `uv run tools/check_schemas.py`, then `schemas/import-lists.console.js` (README **Creating the lists**). All nine lists are new. Add the real values for the master lists (IN-02, IN-03) and the people in `ITH_UserRole`.
2. **Import** the managed ZIP in the portal: Solutions → Import solution → Browse → Next → Next. Use the unmanaged ZIP in Dev only.
3. **In the wizard**, bind the connection references (`ith_sharepoint`, `ith_office365outlook`, the service account's connections) and set the environment variables: site = the project site URL; the nine list variables (each list on that site); `ith_NotificationMailbox` = the sending mailbox (IN-04, blank = the flow owner); `ith_AppLink` = the app's URL; `ith_MailOverride` = a tester mailbox in Dev and Test, **blank in Production**.
4. **After import**: turn the three flows on. **First import of this app version**: open the app in Studio from the solution, **Save**, **Publish** (PA-T8). Add each list as a data source from inside the solution (PA-T13, *Automatically create environment variables* on), set the **data row limit to 2,000**, run OnStart, read **App checker → Formulas** and fix what it shows, then `uv run tools/pp.py export`. Build the attachments control (S-ATT).
5. **Share** the app with the Requester, Technician and Administrator groups (IN-01); set the list permissions (`specs/data-model.md` §1).
6. **Smoke test**: sign in as each role; create a ticket; assign it; change its status; comment; confirm three emails arrive at the override mailbox; open the email link.
7. Record the release in PROJECT.md §7.
