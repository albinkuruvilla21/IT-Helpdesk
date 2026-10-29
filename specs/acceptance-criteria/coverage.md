# Coverage map: IT Help acceptance criteria

Drafted 2026-10-29 by `/acceptance-criteria`. Workbook: `ITH_AcceptanceCriteria.xlsx` (version 0.1, status **In review**, 44 criteria). Scope basis: *everything in the BRD is in scope* (D-02), so no row is a `Candidate`. The prototype is the UI specification; `specs/prototype-fidelity.md` has every prototype element with its AC IDs.

Evidence: **both** = BRD and prototype; **BRD only**; **design only**. There is no transcript.

## 1. BRD rows

Cited `BRD: Helpdesk_BRD 1.0!R<row>` (Excel row).

| Source | Requirement (short) | Evidence | AC IDs | Note |
|---|---|---|---|---|
| R2 | Solution architecture, platform, assumptions, out of scope list | BRD only | AC-ITH-01 | Out-of-scope list written as a not-built check |
| R2 | Mobile-specific layout and dark theme out of scope | both (conflict) | AC-ITH-08, AC-ITH-10 | Q-04 |
| R3 | Left navigation with counts | both | AC-ITH-02 | |
| R3 | Collapsible sidebar | both | AC-ITH-03 | "Subject to control support" |
| R3 | Header: title, global search, notification indicator, profile menu | both | AC-ITH-04, 05, 06, 07 | |
| R3 | Optional Approvals menu (query) | BRD only | none | Q-12; baseline not built, stated in the question |
| R4 | Overview cards, recent tickets, status and priority summaries, assigned tickets, activity feed | both | AC-ITH-11, 12, 13, 14 | Q-06, Q-18 |
| R5 | Ticket list, search, filters, sort, page size, clear, empty state | both | AC-ITH-15, 16, 17, 18 | Q-07 |
| R6 | Create ticket form and automatic ID, status Open, confirmation | both | AC-ITH-20, 21 | Q-09, Q-10, Q-21 |
| R7 | Validation messages | both | AC-ITH-22 | |
| R8 | Attachments | both (prototype simulates) | AC-ITH-23 | Q-14 |
| R9 | Ticket detail view | both | AC-ITH-24 | |
| R10 | Update status, priority and assignment, logged | both | AC-ITH-25 | Q-13 |
| R11 | Edit ticket details | both | AC-ITH-26 | Q-08 |
| R12 | Comments and activity timeline | both | AC-ITH-27, 28 | |
| R13 | Resolve and close | both | AC-ITH-29 | Q-13, Q-20 |
| R14 | Delete after confirmation, Administrator only | both | AC-ITH-30 | Prototype lets anyone delete; BRD wins. Q-11 |
| R15 | My tickets and Assigned to me | both | AC-ITH-19 | |
| R16 | Ticket assignment, technician list | both | AC-ITH-31 | Auto-assignment not built (Q-13) |
| R17 | Outlook notifications | BRD only | AC-ITH-32, 33, 34 | Q-15, Q-19. Scope basis puts it in; the prototype shows only the in-app bell |
| R18 | Knowledge base list, search, article, create ticket from article | both | AC-ITH-35, 36 | |
| R19 | Master data in SharePoint lists; Settings screen | both | AC-ITH-37, 38 | |
| R20 | Role-based access: Requester, Technician, Administrator | BRD only | AC-ITH-39, 40, 41 | Prototype has one fixed technician. Q-03 |
| R21 | CSV export | BRD only | AC-ITH-42 | Q-17 |
| R23 to R25 | Effort 140 h, rate INR 2,150, cost INR 301,000 | commercial | none | Not scope |
| R27, R29 | Change-request rate, 15-day hypercare, payment terms | commercial | none | Not scope; hypercare is a delivery term |
| Timelines | Indicative 8-week plan | commercial | none | Not scope |

## 2. Prototype behaviour

Every register row (`P-nn`) has an AC ID in `specs/prototype-fidelity.md`. By area:

| P-IDs | AC IDs |
|---|---|
| P-01 to P-15, P-19, P-21 | AC-ITH-02 to 06 |
| P-16, P-131 | AC-ITH-08 |
| P-17, P-18 | AC-ITH-07 |
| P-22, P-23, P-60 (overlay), P-94 | AC-ITH-43 |
| P-20, P-24, P-25, P-26, P-123 | AC-ITH-44 (not built) |
| P-30 to P-39 | AC-ITH-10 to 14 |
| P-40 to P-56 | AC-ITH-15 to 19 |
| P-60 to P-77 | AC-ITH-20 to 23, 26, 36 |
| P-80 to P-93 | AC-ITH-23 to 25, 27 to 30 |
| P-100 to P-106 | AC-ITH-35, 36 |
| P-110 to P-114 | AC-ITH-37 |
| P-120 to P-125 | AC-ITH-39 to 41, 07, 32 to 34, 38, 44, 10, STD-A11Y |
| P-130 to P-142 | AC-ITH-09 (and 08 for the dark scheme) |

## 3. Differences between BRD and prototype

| Topic | What the AC says | Question |
|---|---|---|
| Delete | Administrator only (BRD), not anyone | Q-11 |
| Visibility of tickets | Requesters see only their own (BRD R4, R20); the prototype shows everyone's | Q-06, Q-03 |
| Requester name and email on the form | Only technicians and administrators can change them; the prototype lets anyone | Q-21 |
| Ticket ID | Prototype: highest number plus one starting at HD-1001; AC: item ID with the "HD-" prefix as baseline | Q-10 |
| Dark theme, responsive layout | Drafted as Could, baseline: built | Q-04 |
| Attachments | Real files, not names only | Q-14 |
| Demo features | Not built | Q-05 |

## 4. Assumptions and open questions

There are no `ASSUMPTION` sources: every row cites the BRD, the prototype or both. Where an input was silent, the behaviour is a baseline in a question.

| Q | AC IDs | Question (short) | Baseline |
|---|---|---|---|
| Q-01 | All | Accepted prototype version and date | `index (4).html` as is (file confirmed, date open) |
| Q-02 | 09 | Prototype colours and Inter as the brand | Colours yes; Segoe UI for Inter |
| Q-03 | 01, 05, 39 to 41 | Security groups for the three roles | Three groups named later |
| Q-04 | 08, 10 | Dark theme and responsive layout | Built; no phone layout |
| Q-05 | 37, 44 | Reset demo data, Simulated behaviour card | Not built |
| Q-06 | 11, 12, 39 | Requester counts | Own tickets only |
| Q-07 | 06, 15 to 17 | Ticket volume | Under 2,000 tickets |
| Q-08 | 18, 26 | Who may edit | Technicians and administrators |
| Q-09 | 20, 21 | ID format; requester sets priority | Prototype format; yes |
| Q-10 | 21 | Collision-free ID | Item ID with prefix |
| Q-11 | 28, 30 | Permanent delete | Permanent, Administrators |
| Q-12 | 02 | Approvals menu | Not built |
| Q-13 | 19, 22, 24, 25, 27, 29, 31 | BRD queries (transitions, internal notes, auto-close, queues, auto-assign, extra fields) | None built |
| Q-14 | 23 | Attachment limits | 10 MB, any type |
| Q-15 | 32 to 34 | Email events and mailbox | Three emails, shared mailbox |
| Q-16 | 31, 35, 37, 38 | Articles, categories, definitions, technicians | Prototype's as samples |
| Q-17 | 42 | CSV fields, roles, filters | Nine fields, technicians and administrators, filtered |
| Q-18 | 07, 14 | Activity shown to whom | Tickets the user may see |
| Q-19 | 33, 34 | Email to self | No |
| Q-20 | 29, 39 | Requester closes own ticket | No |
| Q-21 | 20, 27 | Requester on behalf of others; requester comments | Staff only; requesters may comment |

## 5. Client inputs awaited

| IN | For | Item |
|---|---|---|
| IN-01 | STD-PERM | Security group names for Requesters, Technicians, Administrators |
| IN-02 | AC-ITH-35 | Initial knowledge base articles and maintainer |
| IN-03 | AC-ITH-38 | Final categories, priority definitions, technician list |
| IN-04 | AC-ITH-32 | Sending mailbox per environment |

## 6. BRD rows not covered

None are dropped. Commercial rows (R23 to R29, Timelines) and the Approvals query (R3, Q-12) have no AC ID, for the reasons above.
