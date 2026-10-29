# {Client} {Project} — prototype fidelity register

> Started by `/ingest` (stage **G1**) from the accepted prototype; AC IDs added by `/acceptance-criteria`
> (G2); *Built as* and *Status* kept by `/ui-dev` (G7) and `/functionality-dev` (G8); checked by `/verify`
> (check 17). The rules are in `docs/standards/prototype-fidelity.md`.
> One row per element or behaviour the prototype shows. Never delete a row: change its status.

| | |
|---|---|
| Prototype | `inputs/design/…` (version, date accepted) |
| Inventoried | `YYYY-MM-DD` by `/ingest` |
| Views found | n (list them in §1) |

## 1. Views

Every view, including the ones a click reveals.

| View | Prototype reference | Reached from | Becomes |
|---|---|---|---|
| Dashboard | `prototype.html #dashboard` | Start; *Dashboard* tab | `scrDashboard` |

## 2. Register

Kind: `layout` · `control` · `content` · `validation` · `action` · `navigation` · `conditional` · `list` ·
`derived` · `state` · `role` · `responsive` · `style` (the look: schemes, background, chrome, cards, buttons, badges, type scale; prototype-fidelity §8).
Status: `Not built` · `Built` · `Matched` · `Deviation` · `Out of scope` (prototype-fidelity §4).

| P-ID | View | Element or behaviour (verbatim wording in quotes) | Kind | Prototype reference | AC IDs | Built as | Status | Note |
|---|---|---|---|---|---|---|---|---|
| P-01 | Dashboard | Header: title "…", user name right-aligned | layout | `prototype.html header` | AC-CON-01 | `scrDashboard`: `lblHdrTitle`, `lblHdrUser` | Not built | |
| P-02 | New request | *Email* required; message "…" under the field on submit | validation | `prototype.html #frmNew`, `validate()` | AC-CON-04.3 | | Not built | |

## 3. Deviations

Every `Deviation` row, with its design-spec §9 row. The reason must be one prototype-fidelity §6 allows.

| P-ID | Prototype shows | Built as | Reason | design-spec §9 |
|---|---|---|---|---|

## 4. Not in the acceptance criteria

Rows with no AC ID: why, and the proposed change or question that covers each.

| P-ID | Why no AC ID | Proposed change / Q-nn |
|---|---|---|
