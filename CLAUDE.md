# CLAUDE.md

Working rules for Claude Code in this Power Apps project. Read this, then `PROJECT.md`, before doing
anything.

> This folder sits beside the Acies SPFx template and shares nothing with it. Open Claude Code **in
> this folder** (or in a repository created from it) so these rules and `.claude/skills/` apply, not
> the SPFx ones at the repository root.

---

## 1. What this repository is

An **Acies Power Apps delivery project**, created from the Acies Power Apps template. It holds one
client project: its inputs, its specifications, one Power Platform solution (a canvas app, its cloud
flows, environment variables and connection references), its list schemas, and the tool that builds,
checks and deploys the solution.

| Where | What |
|---|---|
| `PROJECT.md` | **Who, what, and where every stage stands.** Read it first, every time |
| `inputs/` | The client's artefacts: BRD, PO transcript, accepted design/prototype (or its Figma file, `specs/figma.json`) (**the UI's specification**, §7), brand guidelines (+ `_converted/`) |
| `specs/` | What we generate: AC workbook (the one artefact the client signs off), prototype fidelity register, design spec, build plan, data model, release notes |
| `canvas/<App>/` | Canvas app source: `Src/*.pa.yaml` + `<App>.msapr` (pac SourceCode layout) |
| `solution/src/` | The solution, unpacked (SolutionPackager format): flows, variables, references, app metadata |
| `releases/` | Every release candidate's managed and unmanaged ZIPs, committed by `/verify release` (G11). Import from here |
| `deployment/` | Optional: per-environment settings files for scripted imports. The deliverable is the ZIP; the importer chooses values in the portal |
| `schemas/` | One CSV per SharePoint list, plus `import-lists.console.js` |
| `docs/` | How we work: `pipeline.md`, `alm.md`, `standards/`, `templates/` |
| `samples/` | Exemplars of every artefact. Copy their shape, never their content. `samples/powerapp/` is a **Studio-built reference app**: the UI is cloned from it or built with its patterns (`docs/standards/ui-patterns.md`) |
| `tools/` | `pp.py` (build, validate, deploy, `fx`), `powerfx.py` (the formula checks, with Microsoft's Power Fx parser through `fxparse.ps1`), `canvas_ui.py` (the screen builder: the reference app's layout techniques plus the patterns that reproduce a prototype's look), `prototype_design.py` (measures an HTML prototype's colours in both schemes, type scale, radii, spacing, shadows and background), `schema_builder.py` and `flow_builder.py` (list schemas and cloud flows from Python), `catalogue.py` (the reuse catalogue), `figma_pull.py` (the design from Figma), `visual_compare.py` (the prototype measured in Chromium, and compared with Studio screenshots) and the Python helpers the skills call; `tests/` for the checks themselves |

## 2. Read these when

| Document | When |
|---|---|
| [PROJECT.md](PROJECT.md) | Always, first |
| [docs/pipeline.md](docs/pipeline.md) | Before running or discussing any stage |
| [docs/standards/dev-standards.md](docs/standards/dev-standards.md) | Before writing or reviewing any app YAML, formula, flow or solution component |
| [docs/standards/powerfx-validation.md](docs/standards/powerfx-validation.md) | **Before writing, changing or reviewing any Power Fx formula, and before saying one works.** The four levels of validation, what each check covers, how to write formulas that pass |
| [docs/standards/prototype-fidelity.md](docs/standards/prototype-fidelity.md) | **Before reading a prototype, and before writing, changing or checking any screen.** How to inspect it, how its parts become native controls, what counts as a reason to differ |
| [docs/standards/ui-patterns.md](docs/standards/ui-patterns.md) | **Before writing or changing any screen.** The layout rules, the numbers and the checklist. Never invent a layout |
| [docs/standards/design-standards.md](docs/standards/design-standards.md) | Any UI work |
| [docs/standards/list-schema-standard.md](docs/standards/list-schema-standard.md) | Anything touching a list |
| [docs/standards/acceptance-criteria-standard.md](docs/standards/acceptance-criteria-standard.md) | Anything touching the AC workbook or tests |
| [docs/standards/flow-standard.md](docs/standards/flow-standard.md) | Any Power Automate work |
| [docs/alm.md](docs/alm.md) | Versioning, environments, building, importing, exporting |
| [docs/standards/powerapps-traps.md](docs/standards/powerapps-traps.md) | When an error makes no sense, and before any build, import or list work |
| The reuse catalogue (`/catalogue`, `tools/catalogue.py`) | Before designing or building any screen, component or flow: something like it may already exist |
| [docs/lessons-learned.md](docs/lessons-learned.md) | **Once at the start of every project**, and when something fails: what went wrong before, what now guards against it, the project start checklist |

## 3. The pipeline is the process

Work moves through stages G0–G11, each run by a skill (`/acceptance-criteria`, `/build-plan`, … — see
[PROMPTS.md](PROMPTS.md)). There is **one approval: the Client PO signs off the acceptance criteria
(G2)**. Before it, stages run one at a time; after it, `/deliver` runs G3–G11 end to end. The rules:

1. **Nothing after G2 starts until G2 is `Approved`** in PROJECT.md §2. If it isn't, stop and say
   so: the Client PO signs it off.
2. **Never set G2 to `Approved`.** Set it to `In review` when the workbook is drafted. The PO signs off.
3. **Mark every other stage `Done` when it finishes** and its checks pass. Nobody approves it; people
   review the release candidate as a whole.
4. **Before sign-off, never start the next stage on your own initiative.** Finish, report, and name the
   next step. After sign-off, `/deliver` carries on through every stage; a stage skill run on its own
   still stops at its own end.
5. **`/deliver` stops only for a real blocker:** a default (§4) it would have to break with no
   compliant alternative, a check it can't make pass, an input it can't do without, or anything that
   would touch a client environment or tenant. Ambiguity is not a blocker: take the narrowest reading,
   mark it 🔶, record the question (§5), and carry on.
6. **The approved acceptance criteria are the scope.** Build what they say. A request that isn't in
   them is a change request: say so, and propose adding it to the AC (status `Draft`, source = the
   request) rather than building it quietly.
7. **After sign-off, never rewrite the AC workbook.** Propose changes; people apply them.

For ad-hoc work outside a stage (a bug fix, a question, a refactor), the standards still apply, and so
does rule 6.

## 4. Acies defaults

Every project follows these unless **PROJECT.md §3 records an override**, with the reason and who
agreed. Meet an unrecorded need to break one? Stop, say so in a sentence, and propose the compliant
alternative.

| # | Default |
|---|---|
| **D1** | **Microsoft Lists are the database.** Apps and flows reach lists through data-source environment variables. Dataverse exists only because solutions need it: no Dataverse tables, no SQL |
| **D2** | **No premium Power Platform.** Only connectors in `pp.config.json` → `allowedConnectors`. No HTTP action or trigger, no custom connector, no Dataverse connector in apps or flows |
| **D3** | **No Azure** (Functions, storage, Key Vault, so no Secret-type variables) unless the client approves it for long-running work, secrets, scheduled jobs or external integration |
| **D4** | **No non-Microsoft SaaS.** If SharePoint and M365 can do it, they do it |
| **D5** | **Screens don't hold business rules twice.** A rule used in more than one place is a named formula (or a component), defined once in `App.Formulas` or the component |
| **D6** | **Permission is enforced by list permissions**, not by hiding UI |
| **D7** | **No secrets** in apps, flows, variables, settings files or git |
| **D8** | **Configuration over code** for anything a business user might change: a list item or an environment variable, never a literal in a formula |
| **D9** | **WCAG 2.1 AA**, always |
| **D10** | **One publisher, set at G0, never changed.** Every component carries its prefix (PA-T1) |
| **D11** | **The client's brand, not Acies'**, through design tokens only: named formulas in `App.Formulas`. No `RGBA()`, `ColorValue()` or hex literals on screens. With no brand guide, **the prototype's colours are the brand, in every scheme it defines** (light and dark). Sizes are plain numbers, never computed from tokens: **measured from the prototype** with `tools/prototype_design.py` (fonts px × scale × 0.75 = points; lengths px × scale) and its label heights; the reference app's numbers in `ui-patterns.md` only where no prototype gives one |
| **D12** | **The toolchain is fixed per project:** the `pac` version and Studio control versions recorded in PROJECT.md §1. Upgrade controls only deliberately, never as a side effect |

## 5. Ask before assuming

Write 🔶 rather than a confident guess. Ask about:

- Anything the approved AC doesn't cover, or covers ambiguously
- Tenant facts: licensing, environments, DLP, service account, who imports into Prod (PROJECT.md §5)
- Whether external users (client guests, partners) touch the app
- Using or extending lists the client **already** has instead of creating new ones
- Anything that would run against a client's environment or tenant: you never do that unasked, and
  never Production

Record each question in PROJECT.md §4.

## 6. Prove the risky thing first

If a feature depends on a connector or control behaving a particular way (delegation of a filter, a
connector action's limits, a control not in Studio's verified set, an embed), it goes in build-plan §7
as a spike, and the spike runs before anything is built on it.

## 7. The prototype is the UI specification

The accepted prototype (`inputs/design/`, typically HTML) is the **primary reference** for the app's
UI, layout, design, interactions and functionality. The goal is to translate it into a working Power
Apps solution, not to design a new one. Full rules: [prototype-fidelity.md](docs/standards/prototype-fidelity.md).

1. **Inspect it thoroughly before building.** Read its source (HTML, CSS, scripts), not only the
   converted text or a screenshot: every view, including the ones a click reveals; every control,
   label, validation and message; every action, navigation path and state. `/ingest` records each in
   the fidelity register, `specs/prototype-fidelity.md`.
2. **Replicate it** with native Power Apps controls and this template's architecture: appearance,
   user flows, validations and behaviour, as closely as the platform allows. Wording verbatim; region
   order, hierarchy and proportions kept; the prototype's control type wherever a native one exists.
3. **Don't redesign, simplify or omit** anything it demonstrates, unless the client decided otherwise
   (an AC row, a recorded PO decision) or a platform limitation forces it (prototype-fidelity §6).
   "Simpler", "faster" or "the library has no pattern for it" is not a platform limitation: extend
   the library (ui-patterns §9). Each deviation gets the closest equivalent that keeps the behaviour,
   and a row in design-spec §9.
4. **Validate the result against it** and fix the discrepancies. Before release every register row is
   `Matched`, `Deviation` or `Out of scope`; `Built` means "not yet compared in Studio".
5. **Match its look, not only its structure** ([prototype-fidelity.md](docs/standards/prototype-fidelity.md) §8): colours in each
   scheme, type scale, radii, spacing, shadows, translucency, background and chrome are **measured**
   (`tools/prototype_design.py`) and built with `canvas_ui.py`'s prototype patterns. The reference app's chrome, sizes or square
   cards are never a reason to differ. The only standing platform limits are backdrop blur and following the device's
   light/dark setting automatically (the scheme is chosen by configuration instead).

How it fits: the AC is drafted from the prototype, so the two agree, and the prototype supplies the
detail a criterion doesn't spell out (building that detail is not scope creep). `ui-patterns.md`
decides **how** a screen is built so Studio lays it out; the prototype decides **what** is on it and
**where**. Accessibility (D9) and the Acies defaults override the prototype, as recorded deviations.

## 8. Scope discipline

**Look before you build.** The Acies Power Apps reuse catalogue is the one list of what Acies has already
built. Every screen, component and flow is checked against it (build-plan §1.1), and what a project builds that
others could reuse goes back into it (`/catalogue contribute`). Reuse means adapting to our standards and to this
project's toolchain (D12) and connectors (D2), and only as far as the entry's rights allow.

Build the thinnest thing the approved criteria and the prototype need. No speculative screens, no
"while I'm here" features, no extra settings nobody asked for. Flag it the moment a screen grows past
what its AC rows and the prototype describe. Thinnest never means less than the prototype shows (§7).

## 9. Keep the record straight

| Change | Also update |
|---|---|
| A stage finishes | PROJECT.md §2 (your stage → `Done`; G2 → `In review`) |
| A question arises | PROJECT.md §4 |
| A list's columns | `schemas/<List>.csv` **and** `specs/data-model.md`, then `uv run tools/check_schemas.py` |
| A list added | Its data-source environment variable in `solution/src/environmentvariabledefinitions/`, PROJECT.md §6.2 (and the settings files, if used) |
| A design value | `App.Formulas` in `canvas/<App>/Src/App.pa.yaml` **and** `specs/design-spec.md` |
| A screen's scope or split | `specs/build-plan.md` |
| A screen's state or scheme to compare, or a Studio screenshot of it | `specs/visual-map.json` and `specs/screenshots/`; then `uv run tools/visual_compare.py run` |
| A prototype element built, compared, or built differently | `specs/prototype-fidelity.md` (*Built as*, *Status*); a deviation also in `specs/design-spec.md` §9 |
| A reuse decision (an entry suggested, chosen or not used) | PROJECT.md §8 **and** build-plan §1.1 |
| A flow | `solution/src/Workflows/` **and** `specs/data-model.md` §3 |
| A connection reference | `Customizations.xml`, PROJECT.md §6.3 |
| A formula check (`tools/powerfx.py`, `fxparse.ps1`, `powerfx-functions.json`) | A test both ways in `tools/tests/test_powerfx.py`, `docs/standards/powerfx-validation.md` §3; run the tests and `uv run tools/powerfx.py --selftest` |
| A release imported into Test or Prod | PROJECT.md §7 |
| Anything material in the project | `CHANGELOG.md` (newest entries at the top, above the template's own history) |
| A lesson any project could use (a trap, a check, a rule, a library pattern, a tool fix) | The boilerplate, in the same session (§12) |

If source and the Dev environment disagree, say so. `pp.py export` overwrites source; don't let it
silently discard a source-only change.

## 10. Conventions

- British English in documents (organisation, colour, licence). Tables over prose for anything
  comparative. ISO dates (`2026-10-20`). 🔶 for unknowns.
- Naming: dev-standards §1. Every formula or flow step implementing an acceptance criterion cites its
  ID: `// AC-CON-04.2 …` at the end of the Power Fx formula; the AC ID in a flow step's *Notes*
  (`"description"`). In YAML, never write `: ` inside a comment (it breaks YAML): use a space or a dash.
- Before marking any stage `Done`: its own checks, and `uv run tools/pp.py build` if it touched
  `canvas/` or `solution/` (0 errors). `/deliver` ends with the full `/verify release`.
- **Formulas are validated, never assumed** ([powerfx-validation.md](docs/standards/powerfx-validation.md)). Run `uv run tools/pp.py fx`
  after every change to a `.pa.yaml` (0 errors; read every warning), and `pp.py build` before a stage is `Done`. Report the level reached,
  in these words: *"syntax confirmed by Microsoft's Power Fx parser; static checks 0 errors; not yet opened in Studio"*. Never call a formula
  "error-free", "working" or "validated" until Studio's App checker shows 0 formula errors (level 3) and its acceptance checks were walked
  (level 4). If the build says the stdlib parser was used instead of Microsoft's, say so.
- **UI translates the prototype, built from the library, never invented.** What is on a screen and where comes from the prototype (§7); how it is built comes from a Studio-built reference app (`samples/<app>/`) or `tools/canvas_ui.py`, following `docs/standards/ui-patterns.md`; **how it looks, and every size, comes from the prototype's measured design** (`tools/prototype_design.py`, ui-patterns §10). A layout that passes `pp.py build` is not yet proven: say "not yet opened in Studio" until someone has opened it and the errors are fixed. When Studio shows a new kind of error, fix the cause, add a check to `pp.py build` and a trap to `powerapps-traps.md` the same session.
- Commit after every stage: `G4: build plan`.
- Never commit secrets, real client data in sample rows, `dist/`, or anything in `specs/**/_working/`.

## 11. The traps that bite most

Full list: [powerapps-traps.md](docs/standards/powerapps-traps.md).

- A formula Studio refuses **does nothing when it runs, and says nothing** (PA-T26, PA-T27). `pp.py fx` and `build` check syntax with
  Microsoft's parser and the meaning statically: functions, arity, behaviour functions only in `On…`, names, control properties,
  enums, list columns, `Patch`, delegation, variables, flow calls, AC comments (powerfx-validation §3). Studio still has the last word.
- `pac canvas pack` does **not** check control properties; Studio does, and refuses the app (PA2108).
  `pp.py build` checks them against Studio's control templates. Only use controls and versions it can
  check (PA-T17).
- A YAML-packed app must be opened once in Studio, saved and published before users run it (PA-T8).
- Binding the app to a SharePoint list is a Studio step (with *Automatically create environment
  variables* on), not YAML. Formulas can name the list before it is bound (PA-T13).
- Flows import **off**; values never travel inside the solution; one connection reference per
  connector (PA-T3, PA-T4, PA-T9).
- Internal column names are permanent; `Type`, `Description`, `DisplayName` collide (T-3–T-5). Every
  column a delegable `Filter`/`Sort` uses is indexed (T-1, T-9, PA-T14).
- Layout: `LayoutMode` on a container and `Layout` on a gallery are refused (PA-T21); control names are unique per screen (PA-T23); a comment on a quoted formula goes inside the quotes (PA1001). `pp.py build` checks all three. Generated layouts that nest flexible containers lay out badly (PA-T22): use `ui-patterns.md`.
- Lists have no identity column: references are `<Target>Id` Number columns holding the item ID (L2, L3).

## 12. Send what you learn back to the boilerplate

Every project starts from the Acies Power Apps boilerplate
(`https://github.com/Acies-Innovations/acies-powerapps-boilerplate`). A lesson one project pays for, the next should get
for free, so a generic lesson goes back to the boilerplate **in the same session it is learned**, not at the end of the
project.

| Goes back | Where in the boilerplate |
|---|---|
| A Power Apps, Studio, `pac` or SharePoint behaviour that cost a broken import or a wrong guess | `docs/standards/powerapps-traps.md` (the next `PA-Tnn`) and a row in `docs/lessons-learned.md` |
| A Studio error the static checks missed | A check in `tools/powerfx.py` or `tools/pp.py`, with a test both ways in `tools/tests/` (§9) |
| A layout Studio accepted, or one it laid out badly | A pattern or a guard in `tools/canvas_ui.py`, and `docs/standards/ui-patterns.md` |
| A newer Studio or `pac` the project had to move to (D12) | `tools/canvas-control-templates.json`, `tools/powerfx-functions.json` (`--refresh-functions`) |
| A rule that would have prevented a rework | The standard it belongs to (`docs/standards/`), or a skill's steps |
| A fix or feature in a tool under `tools/` with nothing project-specific in it | The same tool (copy it only if the boilerplate's copy is the one this project started from; otherwise merge) |

**Doesn't go back:** client values, names, URLs or decisions; this project's own screens, flows and generators (those
go to the reuse catalogue: `/catalogue contribute`).

How:

1. Work in a clone beside this repository (`../acies-powerapps-boilerplate`); `git pull` first, clone it if it isn't there.
2. Write it for any project: no client names, values or file paths. Name the project only in the changelog.
3. Bump the template version in its `CHANGELOG.md` (patch for a fix, a trap or a rule; minor for a new tool, check,
   pattern or process) and add an entry headed "(from <project>)": what changed and why.
4. Run the boilerplate's own checks: `uv run tools/pp.py build` (0 errors), `uv run python -m unittest discover -s tools/tests`,
   `uv run tools/powerfx.py --selftest`, and `uv run tools/canvas_ui.py --selftest` if the library changed. A new check is
   proved by breaking something on purpose (lessons-learned row 12).
5. Commit and push it when the user agrees to commit this project's change, under the same rules (§10); tell the user
   what went back and the template version.
6. Note the template version in this project's `CHANGELOG.md` entry.

A project is its own repository, made from the boilerplate, so the boilerplate's history holds only template changes.
`/reset-template` (turning a delivered project back into the template) is the fallback for a project that was built
inside the boilerplate itself.

This section is in the boilerplate's own `CLAUDE.md`, so every project made from it carries the instruction.
