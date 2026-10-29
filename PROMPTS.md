# Prompts

Every automation in this template is a **Claude Code skill** in `.claude/skills/<name>/SKILL.md`. The
SKILL.md file *is* the full prompt: what to read, what to do, the rules, how to check the work, and
how to finish. To change how an automation behaves, edit its SKILL.md and add a CHANGELOG entry.

Run a skill by typing its name in Claude Code, **opened in this folder**: `/acceptance-criteria`. Most
take no arguments: they read `PROJECT.md` and the files the previous stage produced.

**There is one approval: the Client PO signs off the acceptance criteria (G2).** No skill signs it
off, and nothing after it runs until it is given. Then **`/deliver` runs G3–G11 in one go**, without
stopping for review. Each of those stages' skills can also be run on its own (for one screen, or to
redo a stage).

## The automations

| # | Skill | Stage | Needs | Reads | Writes |
|---|---|---|---|---|---|
| 0 | [`/project-setup`](.claude/skills/project-setup/SKILL.md) | G0 | — | arguments, toolchain | `PROJECT.md`, renamed solution, starter ZIP |
| 1 | [`/ingest`](.claude/skills/ingest/SKILL.md) | G1 | G0 done | `inputs/**` | `inputs/_converted/` (+ `SUMMARY.md`), `specs/prototype-fidelity.md` |
| 2 | [`/acceptance-criteria`](.claude/skills/acceptance-criteria/SKILL.md) | G2 | G1 done | converted BRD, transcript, design/prototype | AC workbook, `coverage.md`, for the **Client PO's sign-off** |
| ▶ | [`/deliver`](.claude/skills/deliver/SKILL.md) | G3–G11 | **G2 signed off** | everything | runs 3–11 below in order; ends with the release candidate and an outstanding list |
| 3 | [`/design-spec`](.claude/skills/design-spec/SKILL.md) | G3 | G2 signed off | design, brand guide, AC | `specs/design-spec.md`, tokens in `App.Formulas` |
| 4 | [`/build-plan`](.claude/skills/build-plan/SKILL.md) | G4 | G3 done | AC, design spec | `specs/build-plan.md` |
| 5 | [`/list-schemas`](.claude/skills/list-schemas/SKILL.md) | G5 | G4 done | build plan, AC | `schemas/*.csv`, `specs/data-model.md`, list environment variables |
| 6 | [`/scaffold`](.claude/skills/scaffold/SKILL.md) | G6 | G4, G5 done | build plan, schemas, starter | screens, mock data, solution components |
| 7 | [`/ui-dev`](.claude/skills/ui-dev/SKILL.md) | G7 | G6 done | prototype, register, design spec, AC | screens on mock data, register *Built as* and *Status* |
| 8 | [`/functionality-dev`](.claude/skills/functionality-dev/SKILL.md) | G8 | G7 done | AC, data model, schemas | formulas against the lists |
| 9 | [`/flows`](.claude/skills/flows/SKILL.md) | G9 | G5 done | build plan, data model | `solution/src/Workflows/` |
| 10 | [`/test-cases`](.claude/skills/test-cases/SKILL.md) | G10 | G2 signed off | AC | *Test Cases* sheet |
| 11 | [`/verify`](.claude/skills/verify/SKILL.md) | (G11 with `release`) | — (`release`: G8–G10 done) | everything | check report; solution ZIPs in `releases/` + release notes |
| — | [`/status`](.claude/skills/status/SKILL.md) | any | — | PROJECT.md, inputs, workbook, source | report (+ proposed `Reopened` stages) |
| — | [`/catalogue`](.claude/skills/catalogue/SKILL.md) | any (called by G1, G4, `/deliver`) | read access to the catalogue | the Acies reuse catalogue, inputs or build plan | PROJECT.md §8 suggestions; `specs/catalogue/` entries and a pull request to the catalogue |

## What to type

Each line is a complete instruction. The skill supplies the rest.

```text
/project-setup "Contoso" "Site Requests" CON
/ingest
/acceptance-criteria
/acceptance-criteria phase 1 screens only — the BRD's 'Reporting' sheet is out of scope
/deliver
/deliver from G7
/design-spec
/build-plan
/list-schemas
/scaffold
/ui-dev scrNewRequest scrMyRequests
/functionality-dev scrApprovals
/flows
/test-cases
/test-cases AC-CON-03 AC-CON-05
/verify
/verify release
/status
/catalogue search approval email
/catalogue contribute
```

## Supporting prompts

For work between and after the stages. Paste them into Claude Code and fill in the `<…>` parts. They
lean on CLAUDE.md and the standards, so they stay short.

### Studio says the app has errors

```text
Opening the app in Studio shows: "<paste the error, e.g. Src\scrHome.pa.yaml(34,13) : error PA2108 …>".
Find the cause in canvas/<App>/Src, fix it using the control's real property (dev-standards §2), and
run python tools/pp.py build until it has 0 errors. If pp.py didn't catch it, say why and propose the
check that would have (docs/standards/powerapps-traps.md, tools/pp.py).
```

### Someone changed the app in Studio

```text
<Who> changed <what> in the Dev environment. Run uv run tools/pp.py export, review the diff against
the approved AC and the standards (tokens only, accessible names, delegable queries, AC IDs in
comments), and tell me what changed, what breaks a rule, and what to fix before the next release. Don't
commit yet.
```

### A failed test case

```text
Test case <TC-ID> failed: "<tester's comment>". Find the cause in the screen or flow that implements its
AC (<AC-ID>, check <n>). Fix it without changing behaviour that other checks rely on, keep the AC
reference in the formula or step notes, and run /verify checks 1, 3, 5 and 6. Then tell me what was
wrong and what the tester should re-test. Don't update the workbook: the tester records the re-test.
```

### Apply an approved change to a criterion

```text
The PO approved this change to <AC-ID>: "<change>". It is recorded in the workbook as Changed, with an
Alterations line dated <date>. Run /status to list what it affects, then update only those screens,
flows, schemas and tests, following the usual stage rules: a schema change goes through /list-schemas, a
test change through /test-cases. Show me the plan before you edit anything.
```

### A request that isn't in the acceptance criteria

```text
The client asked for "<request>". Check whether any approved criterion already covers it. If one
does, tell me which. If none does, draft it as a new criterion row in the AC format (status Draft,
source "Change request <date> — <who>"), with its checks, screen, data and impact on the build
plan, for the PO to approve. Don't build anything yet.
```

### Review a pull request

```text
Review the changes on this branch against docs/standards/dev-standards.md, design-standards.md,
flow-standard.md and the acceptance criteria they claim to implement. Report findings in order of
severity: what's wrong, where, which rule or AC check it breaks, and the fix. Include any AC check the
branch claims but doesn't implement.
```

### Onboard a developer joining mid-project

```text
I'm new to this project. Using PROJECT.md, the specs and the source, explain: what we're building and
for whom, where each stage stands, how the app is organised (screens, named formulas, lists, flows,
variables), the environments and how a release gets there, the decisions in PROJECT.md §3 that differ
from the Acies defaults, and the open questions. Keep it to what I need to start work today.
```

### Prepare a demo build

```text
Prepare a demo build for <environment>: version bumped, uv run tools/pp.py build. List what the demo will and won't show, by AC ID, and the values the importer must choose in the wizard, and the steps after import (open
in Studio, save, publish; bind lists; turn flows on). Don't change any behaviour.
```

### Feed a lesson back into the template

```text
On this project we learned: "<what happened, the error, the cause, the fix>". Draft the change to the
Acies Power Apps template that would have prevented it (a new trap in
docs/standards/powerapps-traps.md, a rule in a standard, a step in a skill, or a check in tools/pp.py),
plus its CHANGELOG entry, so I can propose it to the template repository.
```
