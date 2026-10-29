---
name: acceptance-criteria
description: Stage G2. Drafts the acceptance criteria workbook (.xlsx) from the converted BRD, PO transcript and accepted design, in the Acies AC format, with sources, open questions and a BRD coverage map. Use when the user runs /acceptance-criteria or asks to create or draft acceptance criteria.
argument-hint: "[optional notes, e.g. 'phase 1 only']"
disable-model-invocation: true
---

# /acceptance-criteria: stage G2

You are drafting the contract the client's Product Owner will sign. Every criterion must be
traceable to something the client said, or plainly labelled as an assumption. **Completeness and honesty
matter more than polish.**

## 0. Before you start

`PROJECT.md` §2: **G1 must be `Done`.** Otherwise stop and say so.

Then check `specs/acceptance-criteria/`:
- **No workbook yet:** carry on.
- **Workbook exists, every row `Draft`:** ask before replacing it.
- **Workbook exists with any `Approved`, `Changed` or `In Review` row:** do **not** rebuild it. Go to §6
  (change proposal) instead.
- **A reviewed copy has come back** (the PO or BA edited a workbook, or sent a different file): go to §6a.

**Scope basis.** `PROJECT.md` §3 must say what counts as scope. If it doesn't, ask once, and record the
answer as D-nn. The default to propose: *a feature is in scope if the accepted design shows it or the PO
walkthrough describes it; a feature only the BRD mentions is a Candidate.* Without a recorded basis the
draft fills with BRD-only rows padded with assumptions, and the review cuts them.

**Accepted design.** The inputs README asks for the *accepted* design. If `SUMMARY.md` doesn't say which
design version the client accepted, and when, stop and ask. A review against a newer design makes every
"as shown in the design" check wrong.

## 1. Read, in this order

1. `docs/standards/acceptance-criteria-standard.md`: the format and writing rules. Follow it exactly.
2. `samples/acceptance-criteria/Sample_AcceptanceCriteria.json`: the JSON shape and the level of detail expected.
3. `PROJECT.md`: code, list prefix, §3 decisions, §4 questions already asked.
4. `inputs/_converted/INDEX.md` and `SUMMARY.md`.
5. The converted BRD, **every sheet, every row**.
6. The transcript, if there is one.
7. The design or prototype: `specs/prototype-fidelity.md` (the register `/ingest` wrote), the original
   HTML and its scripts, converted PDF **and** every PNG (look at them). The prototype is the UI's
   specification (CLAUDE.md §7): what it demonstrates must reach the criteria.
8. Brand guidelines: only for content facts (logo variants, wording), not visual values.

## 2. Build the requirement inventory first

Before writing any criterion, list every requirement-bearing BRD row (`BRD: <Sheet>!R<n>`), every
transcript topic and every prototype register row (`P-nn`) that carries behaviour (actions,
validations, navigation, conditional display, lists, derived values, states, roles). This list becomes
`specs/acceptance-criteria/coverage.md` (§5). It is how the PO checks nothing was dropped.

Tag each item with its **evidence**: *design*, *transcript*, *both*, or *BRD only*. Per the scope basis:

| Evidence | Row status | Written as |
|---|---|---|
| Design and/or transcript | `Draft` | A full criterion |
| BRD only | `Candidate` | A short row: what the BRD says, a source, and a question "promote into scope, or leave out?" with the baseline "not built". No invented checks, no ASSUMPTION padding |

A speaker who says "retract the last statement" withdraws it: drop it everywhere (checks, Client Inputs,
notes), and where the retraction rules out work, add a check that says so (§3).

When sources disagree:

| Conflict | Do |
|---|---|
| Transcript refines the BRD (more detail, same intent) | Use the detail; cite both |
| Transcript contradicts the BRD | Write what the transcript says, cite both, and add an Open Question asking the PO to confirm |
| Design shows something the BRD doesn't mention | Write it, source = the design, and add an Open Question if its behaviour isn't evident |
| BRD requires something the design doesn't show | Write it; Open Question on how it should look |

## 3. Write the criteria

Follow the standard's §3 (IDs) and §4 (writing). For every row:

- **Area codes:** one per screen or module (`HOME`, `REQ`, `APPR`, `NOTIFY`…). Not for accessibility,
  permissions or states: those are Delivery Standards (below).
- **Acceptance Checks:** numbered, one observable outcome each. Put a number in only when an input gives
  it (a count in the design, a limit the PO stated). Where no input does, cite the design element ("as
  shown in Home 18.pdf, Quick Links") or write the question with a current baseline. Never invent a limit
  and present it as the client's. Behaviour specific to the feature (what happens at 0 items, a missing
  link, long text) stays in the checks; the generic loading/empty/error/permission behaviour does not.
- **Data facts are checks.** When the walkthrough says two features read the same list, who maintains a
  list, how often it changes, or that something is *not* built (no import, no sync, no sign-up box), write
  it as a check as well as in the Data column. The PO reads checks, not the Data column. For every
  client-maintained list, one check: who keeps it up to date, and that no admin screen, import or sync is
  built unless a criterion says so.
- **Power Apps Component:** `<App>: scr<Name>` for a screen, `<App>: conHeader (every screen)` for
  something on every screen, `<App>: App` for app-wide behaviour, `Flow: <display name>` for a flow.
  `<App>` is the app's PascalCase name. Use the same name for every row it implements
  (`docs/standards/design-standards.md` §4 has the mapping rules).
- **Data:** `<PREFIX>_<Entity>: Field, Field, …` using the project prefix, PascalCase field names, and no
  reserved names (`Type`, `Description`, `DisplayName`…). Write "None" when there is no data.
- **Source:** precise (`BRD: Home!R4; Transcript 00:14:32; Design: home.html .hero`). If no input says
  it: `ASSUMPTION — <why it seems needed>` **plus** an Open Question. Once the PO decides it, the Source
  becomes `PO decision YYYY-MM-DD (Q-nn)` and the assumption goes.
- **Client Input Needed:** IN-ids only (`IN-04, IN-05`). The detail goes in `clientInputs`.
- **Open Questions:** Q-ids only (`Q-12`). The question itself goes in `questions`, with the *why it
  matters* and the **current baseline**: what gets built if nobody answers. The same Q-ids go to
  PROJECT.md §4.
- **Status:** `Draft` (`Candidate` for BRD-only). The tool's statuses are `Candidate`, `Draft`, `In
  Review`, `Approved`, `Changed`, `On Hold`, `Out of Scope`.

**Delivery Standards** (`standards` in the JSON, copied from the sample and adapted): accessibility
(WCAG 2.1 AA, default D9), the loading/empty/error/no-permission states (design standard §5), and
permissions by list permissions (default D6). They apply to every criterion, are not scope for the PO to
trade away, and are tested once per component. Don't repeat them in each row, and don't write them as
`AC-` rows: a reviewer who cuts "technical" rows would remove them. If a standard needs the client's
input (the group names), add a client input against the `STD-` id.

`references`: one row per input file. Never a credential. `project`: name, client, code, version `0.1`,
`preparedBy` "Claude Code (/acceptance-criteria)", `preparedOn` today, approval fields empty.

## 4. Build and check

1. Write the JSON (`project`, `acceptanceCriteria`, `standards`, `questions`, `clientInputs`, `references`) to
   `specs/acceptance-criteria/_working/<CODE>_AcceptanceCriteria.json`.
2. `uv run tools/ac_workbook.py build specs/acceptance-criteria/_working/<CODE>_AcceptanceCriteria.json specs/acceptance-criteria/<CODE>_AcceptanceCriteria.xlsx`
3. `uv run tools/ac_workbook.py check specs/acceptance-criteria/<CODE>_AcceptanceCriteria.xlsx`. Fix
   until **0 errors**. (Warnings about missing test cases are expected at this stage.)

## 5. Coverage map

Write `specs/acceptance-criteria/coverage.md`: a table of every inventory item from §2:
`Source | Requirement (short) | AC IDs | Note`. Any item with no AC ID needs a reason in Note (duplicate of
X, out of scope per BRD row Y…). Then list the open questions and assumptions in one place.

Then fill the **AC IDs** column of `specs/prototype-fidelity.md` for every row. A behaviour the
prototype demonstrates is never dropped silently: a row with no AC ID goes in the register's §4 with
the reason and the question that asks the PO. Validations and messages the prototype shows become
checks with the message quoted (`shows "Enter a valid email" under Email`). Presentational rows
(layout, wording) may map to the screen's criterion with a check "as shown in <file> <view>".

The workbook is the one working copy people review. Say so in your reply, and ask the PO to edit that
file in Excel, not to send a second copy.

## 6. Change proposal (workbook already in review or approved)

Don't touch the workbook. Compare the current converted inputs with it, and write
`specs/acceptance-criteria/proposed-changes-<YYYY-MM-DD>.md`: for each difference, the AC ID (or "new"),
the proposed change, the source, and the downstream impact (components and lists named in that row).
The BA and PO apply accepted changes in Excel (status `Changed`, a dated Alterations line).

## 6a. A reviewed copy comes back

1. Put the file in `specs/acceptance-criteria/` unchanged, and name it in the reply.
2. `uv run tools/ac_workbook.py check <reviewed>` and
   `uv run tools/ac_workbook.py diff <current .json or .xlsx> <reviewed> --out specs/acceptance-criteria/_working/review-<date>.md`.
3. Read the diff. The *Needs fixing* list is the first job: deleted rows (restore them as `Out of Scope`),
   dropped sheets, statuses outside the format, content moved to sheets the tool doesn't know.
4. Build **one** merged workbook from the reviewed content plus what it dropped. Keep the reviewer's
   decisions, wording and status changes. Don't revert them, and don't regenerate over them.
5. For every decision the reviewer made: set the Source to `PO decision <date> (Q-nn)`, mark the question
   `Answered`, and write a dated Alterations line (`YYYY-MM-DD · who · what`).
6. If two reviewers worked on different copies, diff both against the base and merge. Where they
   conflict, list it for the PO. Don't choose.
7. Re-read the diff for lost checks. A reviewer who shortens "as shown in the design" may also drop
   behaviour that the standards or other rows still need.
8. Update PROJECT.md §4 from the `questions` sheet. G2 stays `In review`: the merged workbook goes back
   to the PO.

## 7. Self-review before you finish

Re-read every row against the standard's §4 table. In particular: no vague words ("user-friendly",
"fast", "appropriate"), every check testable, every assumption has a question, every data list uses
the prefix. Fix what fails. Then:

- Read the transcript once more for **data statements** ("both read the same list", "the client keeps it
  up to date") and **withdrawals** ("retract the last statement", "ignore this"). Each is a check, or its
  absence is a check.
- Every number in a check traces to an input or sits in a question's baseline.
- No retracted statement survives anywhere, including Client Inputs notes.
- No BRD-only item is `Draft`.
- Every prototype register row has an AC ID or a §4 entry. No criterion describes a screen, control or
  flow differently from the prototype without an Open Question saying so.

## 8. Finish

- PROJECT.md G2 → `In review`; add the open questions to §4 (IDs `Q-nn`, cross-referenced to AC IDs).
- Reply with: counts by area, type and priority; the number of Candidates and assumptions; the open
  questions, listed with their baselines; the client inputs awaited; any BRD rows not covered and why. End with: "The PO reviews and signs
  this off in the workbook (Read Me → Approved by/on) and PROJECT.md G2. I don't sign it off. It is the
  only approval: once it's given, `/deliver` builds everything else to a release candidate."
