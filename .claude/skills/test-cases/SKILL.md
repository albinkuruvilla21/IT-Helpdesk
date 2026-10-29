---
name: test-cases
description: Stage G10. Writes test cases for every approved acceptance check into the Test Cases sheet of the AC workbook (positive, negative, edge, boundary and accessibility), without touching anything else in the workbook. Use when the user runs /test-cases or asks for test cases.
argument-hint: "[optional: AC IDs or areas to cover — default: all live criteria without tests]"
disable-model-invocation: true
---

# /test-cases: stage G10

Testers execute these against the build, and the client sees the results at UAT. Write them for
someone who has never seen the project.

## 0. Before you start

`PROJECT.md` §2: **G2 must be `Approved`.** It needs nothing else, so it can also be run on its own,
alongside development.

## 1. Read

`docs/standards/acceptance-criteria-standard.md` §6 · the sample workbook's test cases
(`samples/acceptance-criteria/Sample_AcceptanceCriteria.json` → `testCases`) ·
`uv run tools/ac_workbook.py dump <workbook> --format json` (existing tests included) · `specs/design-spec.md`
for states and widths · `specs/data-model.md` for the data a precondition needs.

## 2. Write

Scope: `$ARGUMENTS`, or every live criterion (`Approved`/`Changed`) whose checks have no test yet.

For **each check**:
- At least one *Positive* test that proves it.
- A *Negative*, *Edge* or *Boundary* test for every input, limit or failure it implies: zero items,
  maximum items plus one, missing value, long text, no permission, list unavailable, a flow that fails.
- Per screen, one *Accessibility* test (keyboard-only pass; screen-reader names) citing `STD-A11Y`,
  and per data-backed screen one test each for the loading, empty, error and no-permission states
  citing `STD-STATES`, and one permissions test citing `STD-PERM`. Per flow, one test that it runs
  end to end on a new item or schedule, and one for its failure path. The Delivery Standards sheet is
  where those behaviours are specified. They aren't repeated in each criterion.

Each test: `TC-<AREA>-NNN` (continue from the highest existing number in that area), the AC ID **and
check number**, a one-line scenario, preconditions including the exact data needed, numbered
reproducible steps, one expected result, `Status` `Not Run`, `Iteration` empty. If the test depends on
something the client owes (an `Awaiting` client input), add the Input ID to Comments.

Don't re-test what SharePoint or Power Apps itself guarantees (that a list saves an item, that a
button is clickable). Test what this app and its flows do.

## 3. Add and check

1. Write `{"testCases": [...]}` to `specs/acceptance-criteria/_working/tests-<YYYY-MM-DD>.json`.
2. `uv run tools/ac_workbook.py append-tests <workbook> <that file>`: this keeps every other cell.
3. `uv run tools/ac_workbook.py check <workbook>`: 0 errors. Any remaining "no test case" warning
   needs a reason in your reply.

## 4. Finish

PROJECT.md G10 → `Done`. Reply with: tests added per area and type, checks deliberately not tested
and why, and tests that will be blocked on client inputs.
