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
| G1 | Inputs converted | `inputs/_converted/INDEX.md` | `/ingest` | G0 | Not started |
| **G2** | **Acceptance criteria: Client PO sign-off** | `specs/acceptance-criteria/<CODE>_AcceptanceCriteria.xlsx` | `/acceptance-criteria` | G1 | Not started |
| G3 | Design spec | `specs/design-spec.md`, tokens in `App.Formulas` | `/deliver` | G2 | Not started |
| G4 | Build plan | `specs/build-plan.md` | `/deliver` | G3 | Not started |
| G5 | List schemas | `schemas/*.csv`, `specs/data-model.md`, list environment variables | `/deliver` | G4 | Not started |
| G6 | Scaffold | `canvas/` screens, solution components wired, samples removed | `/deliver` | G5 | Not started |
| G7 | UI | Screens against sample data | `/deliver` | G6 | Not started |
| G8 | Functionality | Formulas against real lists | `/deliver` | G7 | Not started |
| G9 | Flows | `solution/src/Workflows/` | `/deliver` | G5 | Not started |
| G10 | Test cases | *Test Cases* sheet of the AC workbook | `/deliver` | G2 | Not started |
| G11 | Release candidate | `dist/<Solution>_<version>_managed.zip` + `specs/release-notes.md` | `/deliver` | G8, G9, G10 | Not started |

**G2 signed off by · on:** 🔶 (the Client PO's name · `YYYY-MM-DD`, matching the workbook's Read Me)

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

## 4. Open questions

| ID | Raised | Question | Raised by | Owner | Answer · date |
|---|---|---|---|---|---|
| Q-01 | | | | | |

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
| `ith_SampleList` | Data source (list, child of the site) | The starter's sample list | 🔶 | 🔶 | 🔶 |
| `ith_SupportEmail` | Text | Where the starter flow sends its notification | 🔶 | 🔶 | 🔶 |

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
