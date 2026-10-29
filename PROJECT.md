# Project card

The one page that says what this project is, where each stage stands, and what it does differently
from the Acies defaults. **Every skill reads this file first.** People edit it; skills update only the
rows they are told to (§2 "Status", never G2's *Approved*; §4 new questions; §7 releases).

`uv run tools/pp.py setup` fills §1's identity rows. 🔶 marks something not yet confirmed. Leave it
showing until someone confirms it; a guess written as fact is worse than a visible gap.

---

## 1. Identity

| Field | Value |
|---|---|
| Client | Acies Innovations |
| Project | IT Help |
| Project code | ITH |
| List prefix | ITH |
| Solution unique name | AciesInnovationsITHelp |
| Solution display name | Acies Innovations IT Help |
| Publisher | AciesInnovations |
| Publisher prefix | `ith_` |
| Canvas app | IT Help |
| Dev environment | 🔶 not set |
| Dev site | 🔶 not set |
| Production site(s) | 🔶 |
| Product Owner (client) | 🔶 |
| Acies delivery lead | 🔶 |
| Code ownership | Acies (default). If the contract gives the client the code, write `Client`, the contract and who checked it |
| Toolchain | Power Platform CLI (`pac`) 2.13+ · uv (Python 3.12, pinned by `.python-version` and `uv.lock`) · Power Apps Studio (document format 1.349 or later) |

The publisher prefix is **permanent**: every environment variable, connection reference and app
carries it, and a component can never move to another publisher (PA-T1).

## 2. Stages

**One sign-off, then one run.**

1. G0–G2 run one at a time. Each starts once the one before it is *Done*; nobody approves G0 or G1.
2. **The Client PO signs off the acceptance criteria (G2).** It is the only approval in the pipeline.
   Only a person sets G2 to *Approved*, and records who and when below. Signing off is a statement
   that the PO read the workbook, not that a tool ran.
3. `/deliver` then runs G3–G11 end to end, marking each stage *Done* as it finishes, without stopping
   for review. People review the release candidate as a whole before anyone deploys it.

| # | Stage | Artefact | Run by | Needs | Status |
|---|---|---|---|---|---|
| G0 | Project set up | This file, renamed solution | `/project-setup` | — | Done |
| G1 | Inputs converted | `inputs/_converted/INDEX.md` | `/ingest` | G0 | Done |
| **G2** | **Acceptance criteria: Client PO sign-off** | `specs/acceptance-criteria/<CODE>_AcceptanceCriteria.xlsx` | `/acceptance-criteria` | G1 | Approved |
| G3 | Design spec | `specs/design-spec.md`, tokens in `App.Formulas` | `/deliver` | G2 | Done |
| G4 | Build plan | `specs/build-plan.md` | `/deliver` | G3 | Done |
| G5 | List schemas | `schemas/*.csv`, `specs/data-model.md`, list environment variables | `/deliver` | G4 | Done |
| G6 | Scaffold | `canvas/` screens, solution components wired, samples removed | `/deliver` | G5 | Done |
| G7 | UI | Screens against sample data | `/deliver` | G6 | Done |
| G8 | Functionality | Formulas against real lists | `/deliver` | G7 | Done |
| G9 | Flows | `solution/src/Workflows/` | `/deliver` | G5 | Not started |
| G10 | Test cases | *Test Cases* sheet of the AC workbook | `/deliver` | G2 | Not started |
| G11 | Release candidate | `dist/<Solution>_<version>_managed.zip` + `specs/release-notes.md` | `/deliver` | G8, G9, G10 | Not started |

**G2 signed off by · on:** Albin . 2026-10-29 (the Client PO's name · `YYYY-MM-DD`, matching the workbook's Read Me)

Status values: `Not started` · `In progress` · `Done` · `Reopened` (an upstream artefact changed after
the stage was done — see `/status`). G2 instead goes `In review` (with the PO) → `Approved` (signed off).
Each `/deliver` stage can also be run on its own with its skill (`/ui-dev`, `/flows`, …), for example
to redo one screen.

## 3. Decisions and overrides

The Acies defaults are in [CLAUDE.md](CLAUDE.md) §4. A project may override one only by recording it
here, with the reason and who agreed. A skill that meets an unrecorded need to break a default stops and
asks.

| ID | Date | Decision (and the default it overrides, if any) | Why | Agreed by |
|---|---|---|---|---|
| D-01 | | 🔶 Publisher: Acies' own (`AciesInnovations`) or one in the client's name | | |
| D-02 | 2026-10-29 | Scope basis: everything in the BRD is in scope. The default (a BRD-only feature is a Candidate until the PO promotes it) is not used, so every AC row is `Draft` | The Acies delivery lead wants the BRD delivered in full | Acies delivery lead (instruction to Claude, 2026-10-29) |
| D-03 | 2026-10-29 | Roles come from a SharePoint list (`ITH_UserRoles`: employee email, role) until the client gives security groups (Q-03). The list is read for what the app shows; list permissions still enforce (D6) once groups exist | The client said to handle groups later | Albin (PO), workbook Q-03 |
| D-04 | 2026-10-29 | No ticket delete: tickets are only closed and kept for audit (Q-11). AC-ITH-30 and the delete part of AC-ITH-41 are not built; change proposed | The PO answered Q-11 after the criteria were drafted | Albin (PO), workbook Q-11 |

## 4. Open questions

| ID | Raised | Question | Raised by | Owner | Answer · date |
|---|---|---|---|---|---|
| Q-01 | 2026-10-29 | Which version of `index (4).html` did the client accept, and when? Every "as shown in the design" depends on it. Baseline: the file in `inputs/design/` as it is | /ingest | Client PO | `index (4).html` confirmed as the accepted design by the Acies delivery lead · 2026-10-29. The date the client accepted it is still open |
| Q-02 | 2026-10-29 | No brand guide: may the prototype's colours (indigo accent `#4f46e5`, light and dark) and Inter font stand as the brand? Inter is not a Studio font; baseline: Segoe UI | /ingest | Client PO | Closed, no answer given: baseline applies · 2026-10-29 |
| Q-03 | 2026-10-29 | Which security groups are the Requesters, Technicians and Administrators (BRD R20)? The prototype has one fixed technician user. Baseline: role read from three group-backed list permissions | /ingest | Client admin | Handled later. Now: a SharePoint list of employee email and role (Requester, Technician, Administrator) · 2026-10-29 |
| Q-04 | 2026-10-29 | BRD R2 puts "mobile-specific layout design and dark theme" out of scope, but the prototype has a dark theme toggle and responsive breakpoints. Build the dark scheme? Baseline: build both schemes, chosen by configuration | /ingest | Client PO | Phone layout is out of scope. The dark scheme stays at the baseline · 2026-10-29 |
| Q-05 | 2026-10-29 | Prototype-only items: "Reset demo data" (profile menu, Settings) and the Settings card "Simulated behaviour". Baseline: not built | /ingest | Client PO | Not needed · 2026-10-29 |
| Q-06 | 2026-10-29 | Overview counts: should requesters see helpdesk-wide counts or only their own tickets (BRD R4)? Baseline: their own | /ingest | Client PO | Only their own tickets · 2026-10-29 |
| Q-07 | 2026-10-29 | Expected ticket volume per month (BRD R5)? Decides delegation and indexes. Baseline: under 2,000 items | /ingest | Client PO | 🔶 |
| Q-08 | 2026-10-29 | Who may edit a ticket after it is created: technicians only, or the requester too (BRD R11)? Baseline: technicians and administrators only | /ingest | Client PO | 🔶 |
| Q-09 | 2026-10-29 | Confirm ticket ID format `HD-` + number, and whether requesters may set Priority (BRD R6). Baseline: yes to the format; requesters may set it, as in the prototype | /ingest | Client PO | 🔶 |
| Q-10 | 2026-10-29 | The prototype's ID is "highest number plus one"; two simultaneous creates could clash. Baseline: the ID is the SharePoint item ID with the `HD-` prefix, no separate counter | /ingest | Acies lead | 🔶 |
| Q-11 | 2026-10-29 | Delete: permanent, or close and retain for audit (BRD R14)? Baseline: permanent delete, Administrators only, as the prototype's confirmation says | /ingest | Client PO | Only closed and kept for audit: no delete (conflicts with approved AC-ITH-30, see proposed-changes-2026-10-29.md) · 2026-10-29 |
| Q-12 | 2026-10-29 | BRD R3 asks whether an optional "Approvals" menu is wanted; the prototype has none. Baseline: not built | /ingest | Client PO | No approvals menu needed · 2026-10-29 |
| Q-13 | 2026-10-29 | BRD queries still open: restrict status transitions (R10); technician private notes and internal comments (R9, R12); auto-close Resolved tickets after n days (R13); shared team queues (R15); auto-assignment by category (R16). Baseline: none of them | /ingest | Client PO | 🔶 |
| Q-14 | 2026-10-29 | Maximum attachment size and allowed file types (BRD R8). Baseline: 10 MB, no restriction on type beyond SharePoint's | /ingest | Client PO | 🔶 |
| Q-15 | 2026-10-29 | Which events send Outlook email, and from which mailbox (BRD R17)? Baseline: the five events listed in the BRD, from a shared mailbox 🔶 | /ingest | Client PO | 🔶 |
| Q-16 | 2026-10-29 | Initial knowledge base articles and their maintainer, final categories, priority definitions and technician list (BRD R18, R19). Baseline: the prototype's six articles, five categories and four technicians as sample data | /ingest | Client PO | Administrators manage the lists in SharePoint (partial: the starting content is still awaited) · 2026-10-29 |
| Q-17 | 2026-10-29 | CSV export (BRD R21) is not in the prototype: which fields and roles? Baseline: the nine fields the BRD lists, technicians and administrators | /ingest | Client PO | 🔶 |
| Q-18 | 2026-10-29 | Should the bell and the Recent activity feed show activity from all tickets, or only tickets the user can see (AC-ITH-07, 14)? Baseline: only tickets the user may see | /acceptance-criteria | Client PO | 🔶 |
| Q-19 | 2026-10-29 | Should a person get an email about a change they made themselves (AC-ITH-33, 34)? Baseline: no | /acceptance-criteria | Client PO | 🔶 |
| Q-20 | 2026-10-29 | May a requester close or reopen their own ticket (AC-ITH-29, 39)? Baseline: no | /acceptance-criteria | Client PO | 🔶 |
| Q-21 | 2026-10-29 | May requesters raise a ticket on someone else's behalf, and comment on their own tickets (AC-ITH-20, 27)? Baseline: only staff change the requester; requesters may comment | /acceptance-criteria | Client PO | 🔶 |
| Q-22 | 2026-10-29 | May the dark/light choice be remembered per user (needs a small list)? Baseline: not remembered, starts Light each session (design-spec DEV-02) | /design-spec | Client PO | 🔶 |
| Q-23 | 2026-10-29 | Comments and activity must be readable by the requester of a ticket, so their lists cannot hide other people's items. Accept list-wide read (app filters), or ask for per-item permissions (a flow, out of scope)? Baseline: list-wide read | /list-schemas | Client PO | 🔶 |
| Q-24 | 2026-10-29 | A ticket staff raise for someone else is created by staff, so that requester cannot read it through list permissions (item-level own-items follows the creator). Accept? Baseline: accepted | /list-schemas | Client PO | 🔶 |

## 5. Tenant facts

These make or break features. None of them can be inferred from source. Confirm each one with the
client's admin.

| Fact | Value |
|---|---|
| Licensing: Microsoft 365 seeded Power Apps / Power Automate, or premium | 🔶 (default: seeded only, D2) |
| Environments: who may create them; are Dev, Test and Prod created, each **with a Dataverse database** | 🔶 |
| Dataverse capacity for three environments | 🔶 |
| DLP policy on the target environments: every connector the solution uses in the same group | 🔶 |
| Who imports into Production (client admin or Acies) | 🔶 |
| Service account that owns connections in Test and Prod (licensed, MFA works with connectors) | 🔶 |
| External sharing / guest users of the app | 🔶 |
| Graph / premium connectors approved | None — default |

## 6. Environments and solution components

### 6.1 Environments

Every environment that receives the solution needs a **Dataverse database**: that is where solutions
live. The app's data still lives in SharePoint lists (D1). The URLs also go in `pp.config.json`.

| Environment | URL | Type | Package | SharePoint site | Imported by |
|---|---|---|---|---|---|
| Dev | 🔶 | Sandbox | Unmanaged (the makers' workspace) | 🔶 | Acies |
| Test | 🔶 | Sandbox | Managed | 🔶 | Acies |
| Prod | 🔶 | Production | Managed | 🔶 | 🔶 |

### 6.2 Environment variables

Values are **never** in the solution. The person importing the ZIP chooses each environment's values in
the portal's import wizard (or, for scripted imports, in `deployment/settings.<env>.json`).

| Schema name | Type | Holds | Dev | Test | Prod |
|---|---|---|---|---|---|
| `ith_SharePointSite` | Data source (SharePoint site) | The site holding the app's lists | 🔶 | 🔶 | 🔶 |
| `ith_TicketList` | Data source (list, child of the site) | `ITH_Ticket`: Tickets | 🔶 | 🔶 | 🔶 |
| `ith_TicketCommentList` | Data source (list, child of the site) | `ITH_TicketComment`: Comments on tickets | 🔶 | 🔶 | 🔶 |
| `ith_TicketActivityList` | Data source (list, child of the site) | `ITH_TicketActivity`: Activity timeline and flow trigger | 🔶 | 🔶 | 🔶 |
| `ith_ArticleList` | Data source (list, child of the site) | `ITH_Article`: Knowledge base articles | 🔶 | 🔶 | 🔶 |
| `ith_TechnicianList` | Data source (list, child of the site) | `ITH_Technician`: Technicians for assignment | 🔶 | 🔶 | 🔶 |
| `ith_CategoryList` | Data source (list, child of the site) | `ITH_Category`: Ticket categories | 🔶 | 🔶 | 🔶 |
| `ith_PriorityList` | Data source (list, child of the site) | `ITH_Priority`: Priorities and definitions | 🔶 | 🔶 | 🔶 |
| `ith_StatusList` | Data source (list, child of the site) | `ITH_Status`: Statuses and definitions | 🔶 | 🔶 | 🔶 |
| `ith_UserRoleList` | Data source (list, child of the site) | `ITH_UserRole`: Employee roles (D-03) | 🔶 | 🔶 | 🔶 |
| `ith_NotificationMailbox` | Text | Mailbox the notification emails go from (IN-04, Q-15) | 🔶 | 🔶 | 🔶 |
| `ith_AppLink` | Text | The app's link, for emails (AC-ITH-32) | 🔶 | 🔶 | 🔶 |

### 6.3 Connection references

One per connector. In Test and Prod they bind to the **service account's** connections (§5).

| Logical name | Connector | Connection owner |
|---|---|---|
| `ith_sharepoint` | SharePoint | 🔶 service account |
| `ith_office365outlook` | Office 365 Outlook | 🔶 service account |

## 7. Releases

Newest first. One row per import into Test or Prod.

| Version | Date | Environment | Package | Imported by | Notes |
|---|---|---|---|---|---|
| | | | | | |

## 8. Reuse

What this project reuses, or could. The **Acies Power Apps reuse catalogue** (`tools/catalogue.config.json`)
is the source of truth: `/ingest` adds its matches here as *Suggested*, and `/build-plan` decides every
one in build-plan §1.1. Know of something that isn't in the catalogue? Add it here with its repository
link, and it goes into the catalogue when the project gives back (`/catalogue contribute`).

| Catalogue entry, or repository (URL @ commit) and path | What it does | Could serve (features or AC IDs) | Rights | Status | Notes |
|---|---|---|---|---|---|
| | | | 🔶 | | |

*Rights* come from the catalogue entry: `Acies-owned` (the default), `Client-owned`, `Client-owned (consent
recorded)` or `Open source`. *Status*: Suggested · Chosen (Pattern or Adapt code) · Not used. **Reuse means adapting to
this project's standards**, never pasting in: the toolchain is fixed (D12), connectors stay in `allowedConnectors` (D2), rules live once in
named formulas (D5), colours come from this project's tokens (D11). Acies owns its code unless a contract says otherwise; a
`Client-owned` entry is read for the approach only.
