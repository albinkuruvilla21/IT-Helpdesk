<!-- README:intro -->
# Acies Power Apps delivery template

The starting point for every Acies Power Apps project. Create a project from it, and you have:

- **A working Power Platform solution, kept as source:** a canvas app, a cloud flow, environment
  variables and connection references, built the Acies way (SharePoint lists as the database, standard
  connectors only, design tokens, accessibility). `tools/pp.py build` turns it into a solution ZIP you
  import at [make.powerapps.com](https://make.powerapps.com), and validates it first.
- **A pipeline run by Claude Code:** from the client's BRD, PO walkthrough, accepted design or
  prototype and brand guidelines to acceptance criteria. Once the client's PO signs those off (the one
  approval), a single command, `/deliver`, builds the design spec, list schemas, screens, formulas,
  flows and test cases through to a release candidate.
- **The standards behind it:** development, design, list schemas, acceptance criteria and flows, plus
  the Power Platform and SharePoint traps that cost time.

It mirrors the Acies SPFx template (same stages, same acceptance-criteria workbook, same list
schemas), and shares nothing with it: copy this folder out and use it as a repository of its own.

| Read | For |
|---|---|
| This file | Starting a project, creating lists, building, importing and deploying |
| [docs/pipeline.md](docs/pipeline.md) | How the stages fit together, the one sign-off, where Claude's work meets Studio |
| [PROMPTS.md](PROMPTS.md) | Every automation, how to run it, and the supporting prompts |
| [CLAUDE.md](CLAUDE.md) | The rules Claude works by in this project (worth reading yourself) |
| [docs/alm.md](docs/alm.md) | Environments, versioning, managed vs unmanaged, variables, connections, CI/CD |
| [docs/standards/](docs/standards/) | The standards, and the traps |
| [docs/lessons-learned.md](docs/lessons-learned.md) | What the first project taught: every failure, what guards against it, the start checklist |
| [docs/standards/ui-patterns.md](docs/standards/ui-patterns.md) | How screens are built (read before any UI work) |
| [CHANGELOG.md](CHANGELOG.md) | What changed in the template |

---
<!-- /README:intro -->

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Power Platform CLI (`pac`) | 2.13 or later | `pac`. Install: `dotnet tool install --global Microsoft.PowerApps.CLI.Tool` (needs the [.NET SDK](https://dotnet.microsoft.com/download)), or the *Power Platform Tools* VS Code extension |
| [uv](https://docs.astral.sh/uv/) | current | `uv --version`. Brings the right Python and the tool packages: [Setting up the Python tools](#setting-up-the-python-tools) |
| PowerShell 7 (`pwsh`) | 7.6 or later with pac 2.13 (the same .NET major version as `pac`) | `pwsh --version`. Lets `pp.py` parse every formula with **Microsoft's Power Fx parser**, which ships inside `pac`. Without it the build falls back to a stdlib parser and warns ([powerfx-validation.md](docs/standards/powerfx-validation.md) §7) |
| GitHub CLI | current | `gh auth status`. Lets git push and read the reuse catalogue ([The reuse catalogue](#the-reuse-catalogue)); `gh auth setup-git` if git can't use your sign-in |
| Claude Code | current | `claude --version`. **Open it in this folder**, so this folder's `CLAUDE.md` and skills load |
| Power Platform | A **Dev environment with a Dataverse database** where you are a maker; a SharePoint **dev site** where you have *Manage Lists* | |

`uv run tools/pp.py doctor` checks the toolchain.

## Setting up the Python tools

The tools in `tools/` run through **uv**, which installs the Python in `.python-version` (3.12) and the packages in
`pyproject.toml`, pinned by `uv.lock`, into the repository's own `.venv`. Nothing goes into your Python.

1. Install uv once per machine: `winget install --id=astral-sh.uv -e` on Windows, or `pip install uv`
   ([other ways](https://docs.astral.sh/uv/getting-started/installation/)). Check `uv --version`; if the terminal can't
   find it, add the folder the installer names to your PATH.
2. **From the repository root:** `uv sync`, then `uv run playwright install chromium` (once per machine: the browser
   `tools/visual_compare.py` renders the prototype in). Every `uv run tools/<tool>.py` command also runs from the root; elsewhere uv
   reports `No pyproject.toml found`.

Without uv: Python 3.10+ and `pip install --group tools` (pip 25.1+), from the same `pyproject.toml`. `pac` and
PowerShell 7 are not Python packages and are installed separately (above).

<!-- README:start -->
## Starting a project

1. **Create the repository:** copy this folder into a new **private** repository (it will hold client
   documents). Open Claude Code in it.
2. **Set it up:**
   ```
   /project-setup "Contoso" "Site Requests" CON
   ```
   This names the solution, the publisher prefix (permanent once imported) and the app, regenerates the
   flow and app IDs, fills `PROJECT.md`, and builds the starter ZIP. Without Claude:
   `uv run tools/pp.py setup --client "Contoso" --project "Site Requests" --code CON`, then
   `uv run tools/pp.py build`.
3. **Add the inputs** to `inputs/` ([inputs/README.md](inputs/README.md)):

   | Folder | What |
   |---|---|
   | `inputs/brd/` | The BRD (.xlsx preferred) |
   | `inputs/transcripts/` | The PO walkthrough transcript (.vtt from Teams, or .docx) |
   | `inputs/design/` | The **accepted** prototype: its HTML (best) or the Figma file, plus a PNG per screen ([The design](inputs/README.md#the-design)) |
   | `inputs/branding/` | Brand guidelines, logos |
   | `inputs/other/` | Anything else: list exports, an existing app to replace, process diagrams |

4. **Draft the acceptance criteria:** `/ingest`, then `/acceptance-criteria`. This produces
   `specs/acceptance-criteria/<CODE>_AcceptanceCriteria.xlsx`.
5. **Get them signed off by the client's PO**: in the workbook (Read Me → *Approved by / on*), and in
   `PROJECT.md` §2 (G2 → `Approved`, `Name · YYYY-MM-DD`). **This is the only approval.**
6. **Run `/deliver`.** It runs every remaining stage in order, without stopping for review, and
   commits each one:

| Stage | Skill it runs | Produces |
|---|---|---|
| G3 | `/design-spec` | `specs/design-spec.md` + the client's tokens in `App.Formulas` |
| G4 | `/build-plan` | `specs/build-plan.md` |
| G5 | `/list-schemas` | `schemas/*.csv` + `specs/data-model.md` + a data-source variable per list |
| G6 | `/scaffold` | Every screen as YAML, mock data, solution components; samples removed |
| G7 | `/ui-dev` | Screens on mock data, every state |
| G8 | `/functionality-dev` | Formulas against the real lists |
| G9 | `/flows` | Cloud flows in the solution |
| G10 | `/test-cases` | Test cases in the AC workbook |
| G11 | `/verify release` | Managed + unmanaged ZIPs + `specs/release-notes.md` |

   It ends with a release candidate and an **outstanding list**: what only people can do (import the
   lists, import the solution, open the app in Studio and bind the lists, compare the screens with the
   design, turn the flows on, run the tests). The delivery lead reviews the lot and deploys.

   `/status` tells you where things stand and what's next at any point. `/verify` runs every check
   without releasing. Any stage's skill can be re-run on its own, e.g. `/ui-dev scrNewRequest` after a
   design change.

   Lessons the project learns go back to this template in the same session ([Improving the template](#improving-the-template)).
   `/reset-template` turns a project built inside the template back into the template; a project in its own
   repository never needs it.
<!-- /README:start -->

## Repository layout

```
├── PROJECT.md            project card: identity, stages, decisions, questions, tenant facts, environments
├── CLAUDE.md             rules for Claude Code
├── PROMPTS.md            every automation and supporting prompt
├── CHANGELOG.md
├── .claude/skills/       the automations — one folder per skill, SKILL.md is the prompt
├── inputs/               client artefacts (brd/ transcripts/ design/ branding/ other/) + _converted/
├── specs/                generated documents (AC workbook, design spec, build plan, data model, release notes, visual map, Studio screenshots)
├── canvas/<App>/         canvas app source: Src/*.pa.yaml + <App>.msapr
├── solution/src/         the solution, unpacked (SolutionPackager): flows, variables, references, app metadata
├── deployment/           optional: settings.<env>.json for scripted imports
├── schemas/              one CSV per list + import-lists.console.js
├── docs/
│   ├── pipeline.md · alm.md · reference-analysis.md
│   ├── standards/        dev, design, list schema, acceptance criteria, flow standards; Power Apps traps
│   └── templates/        design spec, build plan, data model, release notes
├── samples/              exemplars: AC workbook, list schema, flow
├── tools/                pp.py · ingest.py · ac_workbook.py · check_schemas.py · catalogue.py · canvas-control-templates.json
├── pp.config.json        build settings: canvas app ↔ source, environments, allowed connectors
├── releases/             every release candidate's solution ZIPs, committed by /verify release
└── dist/                 build output (git-ignored)
```

## The starter solution

`uv run tools/pp.py build` builds and validates it before you change anything. It holds samples, which
`/scaffold` removes once the project's own screens exist:

| Sample | Shows |
|---|---|
| *Starter App* (`canvas/StarterApp/`) | One screen: design tokens as named formulas, a heading role, AC IDs in formula comments |
| *Sample - Notify on new item* (flow) | SharePoint trigger on a variable-driven site and list → email to a variable address; Try/Catch; connection references |
| `<prefix>_SharePointSite` + `<prefix>_SampleList` | The site + list pair of data-source environment variables. The site variable stays |
| `<prefix>_SupportEmail` | A text variable |
| `<prefix>_sharepoint`, `<prefix>_office365outlook` | One connection reference per connector |

## Creating the lists

Lists are created from the CSVs in `schemas/` by **`schemas/import-lists.console.js`**, a script you
paste into the browser. No PnP PowerShell, no app registration, no install. It runs as you, so you need
*Manage Lists* on the target site.

1. Open the target site's **Site contents** page in Edge or Chrome:
   `https://<tenant>.sharepoint.com/sites/<site>/_layouts/15/viewlsts.aspx`
2. Open DevTools (**F12**) → **Console**. If the console refuses the paste, type `allow pasting` and
   press Enter first.
3. Open `schemas/import-lists.console.js`, copy **all** of it, paste it into the console and press Enter.
   A panel titled **List importer** appears, showing the target site's URL. Check that it's the right site.
4. **Choose schema folder…** → select this project's `schemas/` folder. Every CSV is listed and ticked.
5. **Import entries:** tick this to also add each CSV's sample rows. Use it on dev sites; leave it **off**
   on production.
6. **Import into this site** → confirm. The log shows each list, the fields created, and any rows added.

It creates each list named after its CSV, adds missing fields with their exact internal names, indexes
the ones marked `Indexed="TRUE"`, and is safe to re-run. It doesn't set list permissions: set those from
`specs/data-model.md`, or ask the client's admin to. **Before importing, run
`uv run tools/check_schemas.py`** and fix every error.

Note each list's name and the site URL: you choose them in the import wizard (next section).

## Building

```bash
uv run tools/pp.py build          # canvas YAML -> .msapp -> solution ZIPs (unmanaged + managed) -> validate
uv run tools/pp.py validate       # the checks again, on the latest build or any ZIP
```

`build` stops on any failed check. What it checks: the package shape; the solution's identity and
version; every component's files and prefix; **every canvas control property against Studio's own
control templates** (so Studio won't refuse the app, PA-T17); connectors against `allowedConnectors`
(D2), no HTTP; flows use connection references and declared variables; no packaged values, emails,
tenant URLs, SAS tokens or site IDs; and SolutionPackager must accept the ZIP. Warnings (don't fail): a
YAML-packed app that still needs its first save in Studio, more than one reference per connector,
controls whose properties can't be checked.

## Importing

Use the **unmanaged** ZIP for the Dev environment, the **managed** one everywhere else
([docs/alm.md](docs/alm.md) §3).

1. Open [make.powerapps.com](https://make.powerapps.com), pick the target environment (top right).
   It must have a Dataverse database.
2. **Solutions** → **Import solution** → **Browse** → choose the ZIP from `releases/` (a release) or `dist/` (your own build) → **Next** → **Next**.
3. **Connections**: for each connection reference, pick a connection, or create one. In Test and Prod,
   use the service account's connections (PROJECT.md §6.3).
4. **Environment variables**: choose the SharePoint site, then each list; type the text values. You can
   leave them blank and set them later under the solution's *Environment variables*. **This is how the
   solution is delivered: the ZIP carries the variable definitions, the person importing supplies the
   values.** Nothing else is needed.
5. **Import**.

**Optional: scripted import.** For repeatable imports into several environments, put the values in a
settings file and use the command line (see *Deployment settings (optional)* below):

```bash
pac auth create --environment https://<org>.crm.dynamics.com     # once per environment
uv run tools/pp.py import --env dev                              # unmanaged, publishes
uv run tools/pp.py import --env test --activate                  # managed, flows turned on
```

### After every import of a new app version

| Step | Why |
|---|---|
| Open the app in Studio (**Edit**), wait for it to load, **Save**, then **Publish** | The app was packed from YAML; Studio compiles it on first open (PA-T8). If Studio reports an error, give it to Claude: [PROMPTS.md](PROMPTS.md) *Studio says the app has errors* |
| First time a list is used: add it as a data source **from inside the solution**, with *Automatically create environment variables when adding data sources* on (Studio **Settings**) | Binding a list is a Studio step (PA-T13). Formulas already use the list's name |
| Turn the flows **On** | Flows import off |
| Share the app; add run-only users to flows the app calls | Importing shares nothing |
| In Dev only: `uv run tools/pp.py export`, review, commit | Source then holds the Studio-saved app |

## Deployment settings (optional)

**Skip this section if you import through the portal.** Settings files are only for scripted
(`pp.py import`) imports; `build`, `validate` and every skill work without them.

`deployment/settings.<env>.json` holds, per environment, every environment variable's value and the
connection each connection reference binds to. `pac solution import --settings-file` applies it.

```bash
uv run tools/pp.py settings              # regenerates settings.template.json from the built ZIP; checks every file
uv run tools/pp.py settings --env test   # strict: every value filled (import runs this)
pac connection list                      # the connection IDs of the environment you're signed in to
```

| Variable type | Value |
|---|---|
| SharePoint site | The site URL: `https://<tenant>.sharepoint.com/sites/<site>` |
| SharePoint list | The list's ID (*List settings* → the `List=` GUID in the URL) |
| Text | The text |

Environment facts, not secrets: no passwords, keys or tokens ever (D7).

## Day-to-day, and releasing

```bash
uv run tools/pp.py export                # Dev -> solution/src and canvas/ (or --zip <file> exported by hand from the portal)
git diff                                 # review
uv run tools/pp.py bump                  # every package that leaves Dev needs a higher version
uv run tools/pp.py build                 # -> dist/<Solution>_<version>_managed.zip
# a release candidate: /verify release copies both ZIPs to releases/ and commits them. Import from there
```

Import the managed ZIP into Test, then the same ZIP into Production, through the portal (*Importing*
above), or with `pp.py import --env <env> --activate` if you set up settings files.

- `export` also removes what an export carries but source must not: packaged variable values (PA-T4)
  and dev values in flow parameters (PA-T5).
- Add `--upgrade` when a release **removes** components. Record each release in PROJECT.md §7.
- `uv run tools/pp.py check` runs Microsoft's solution checker (needs `pac auth`). Run it before Prod.
- Never fix things directly in Test or Prod (PA-T10). Fix in Dev, release again.

## The reuse catalogue

[Acies-Innovations/acies-powerapps-catalogue](https://github.com/Acies-Innovations/acies-powerapps-catalogue) is
the single source of truth for what Acies has already built in Power Apps: one entry per reusable canvas screen or
component, screen generator, named-formula set, cloud flow or list schema, pointing to its code at a pinned commit,
with **who owns it** (Acies, unless a contract gave a client the code: PROJECT.md §1 *Code ownership*), the `pac` and
Studio versions it was built with (D12) and its connectors (D2). Projects use it without anyone having to remember:

| Stage | What happens |
|---|---|
| `/project-setup` | Fetches the catalogue and checks you can read it (`gh auth setup-git` if git can't) |
| `/ingest` | Suggests entries that match the BRD and prototype: PROJECT.md §8 |
| `/build-plan` | Decides for every screen, component and flow: reuse an entry, or *no match* (build-plan §1.1) |
| `/deliver` | Drafts entries for what the project built that others could reuse, and asks before opening the pull request |

Any time: `/catalogue search <what>`, or `uv run tools/catalogue.py fetch` then `uv run tools/catalogue.py search <words>`.
Its address is in `tools/catalogue.config.json`. The clone lives in `references/` (git-ignored).

## Tools

| Command | Does |
|---|---|
| `uv run tools/pp.py doctor` | Checks Python, `pac`, .NET, `pac auth` |
| `uv run tools/pp.py setup --client --project --code [...]` | Names the project, publisher, app; new IDs; fills PROJECT.md |
| `uv run tools/pp.py bump [--part major\|minor\|build\|revision] [--set X.Y.Z.W]` | Raises the solution version |
| `uv run tools/pp.py fx [--release]` | Checks the canvas source without packing: YAML, control properties, every Power Fx formula ([powerfx-validation.md](docs/standards/powerfx-validation.md)). Run after every edit |
| `uv run tools/pp.py build [--skip-canvas] [--unmanaged-only]` | Packs and validates (formulas included) |
| `uv run python -m unittest discover -s tools/tests` · `uv run tools/powerfx.py --selftest` | Tests the formula checks themselves |
| `uv run tools/pp.py validate [ZIP...] [--no-roundtrip]` | Validates the latest build or any ZIP (e.g. a client's existing solution) |
| `uv run tools/pp.py settings [--env ENV]` | *Optional.* Settings template + completeness check |
| `uv run tools/pp.py import --env ENV [--managed\|--unmanaged] [--activate] [--upgrade] [--yes]` | *Optional.* Validates, checks settings, imports from the command line |
| `uv run tools/pp.py export [--env ENV] [--zip FILE]` | Pulls the solution into source, cleaned |
| `uv run tools/pp.py check` | Microsoft's solution checker |
| `uv run tools/ingest.py [--status\|--all]` | Converts `inputs/` to text in `inputs/_converted/`, with change tracking |
| `uv run tools/ac_workbook.py build\|dump\|append-tests\|check\|diff …` | Builds, reads, extends, checks and compares the AC workbook ([standard §8](docs/standards/acceptance-criteria-standard.md#8-tool-reference)) |
| `uv run tools/check_schemas.py [folder]` | Checks list CSVs against the schema standard |
| `uv run tools/figma_pull.py pages\|pull\|images` | Reads the accepted design from Figma ([The design](inputs/README.md#the-design)) |
| `uv run tools/visual_compare.py measure <screen>\|run [--strict]\|compare …` | Measures the prototype as Chromium renders it; compares each screen with its Studio screenshot (`specs/visual-map.json`, `specs/screenshots/`) |
| `uv run tools/prototype_design.py <file>.html --content <w> [--formulas\|--check …]` | Measures an HTML prototype's look; proposes and checks the tokens |
| `uv run tools/catalogue.py fetch\|list\|search …` | Fetches and searches the [reuse catalogue](#the-reuse-catalogue) |

## Troubleshooting

| Symptom | Likely cause · fix |
|---|---|
| Studio: `error PA2108 : Unknown property …` | A property the control doesn't have. `pp.py build` now catches these (PA-T17); fix the YAML and rebuild |
| Studio: a formula error `pp.py fx` didn't report | The static checks can't bind every type (powerfx-validation §6). Fix the formula, then add a test and a check (§8) |
| Build: *syntax checked by the stdlib parser only* | `pac` or PowerShell 7 not found, or on a different .NET version. Install them; the message says which |
| Import: *"The solution file is invalid"* | The ZIP was re-zipped by hand. Rebuild with `pp.py build` |
| Import: *missing dependencies* | The target lacks something the solution uses. Install it first |
| Import: *a newer or same version is installed* | `pp.py bump`, rebuild |
| Flow suspended or *connection not configured* | A reference has no connection, or DLP blocks a connector (PROJECT.md §5) |
| App shows errors to users after import | Never opened and saved in Studio (PA-T8) |
| `pac` says *not authenticated* | `pac auth create --environment <url>`; `pac auth list` / `pac auth select` |

More: [docs/standards/powerapps-traps.md](docs/standards/powerapps-traps.md).

## Client documents in the repository

By default `inputs/` is committed, so every developer works from the same sources and every
criterion's citation can be checked. That is only acceptable in a **private** repository, and only if
the client's contract allows their documents on GitHub. If it doesn't, uncomment the `inputs/` lines in
`.gitignore` and keep the files on the project's SharePoint site instead. Record which in `PROJECT.md`
§3. Never commit a client's exported solution or `.msapp` unreviewed: it carries tenant URLs, people and
connection IDs (PA-T7).

## Improving the template

A lesson from a project that would help the next one (a new trap, a better prompt, a check `pp.py`
should make, a `canvas_ui.py` pattern) goes back into this template **in the same session it is learned**,
from a clone beside the project: [CLAUDE.md §12](CLAUDE.md#12-send-what-you-learn-back-to-the-boilerplate) says what goes back, where,
and the checks to run. Projects record which template version they started from in their own `CHANGELOG.md`.

Each project is its own repository, made from this one, so this repository's history holds only template
changes. `/reset-template` remains for a project that was built inside the template itself.
