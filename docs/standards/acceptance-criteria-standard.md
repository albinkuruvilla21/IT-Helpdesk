# Acceptance criteria standard

The acceptance criteria (AC) workbook is the contract for a project: the PO signs it off, developers
build to it, testers execute against it, and the client accepts against it at UAT. It is the **scope**.
Nothing is built that isn't in it, and nothing in it is skipped silently.

Worked example: [samples/acceptance-criteria/Sample_AcceptanceCriteria.xlsx](../../samples/acceptance-criteria/Sample_AcceptanceCriteria.xlsx)
(its JSON source sits beside it). Tool: `tools/ac_workbook.py`.

## 1. What changed from the earlier format, and why

The earlier workbook (one AC sheet, then one test sheet per screen) worked for people. These changes
make it work for automation too, without losing anything people relied on.

| Before | Now | Why |
|---|---|---|
| One free-text "Description / Acceptance Criteria" cell mixing layout, data, behaviour and open notes | **Description** (what and why) + **Acceptance Checks** (a numbered list, one observable outcome each) | Each check can be built, traced and tested on its own; a test case cites `AC-CON-01.3` |
| Data source buried in prose ("connected to an SP list…") | **Data (Lists & Fields)** column | `/list-schemas` and `/build-plan` read it directly |
| No link from a criterion to the code | **Power Apps Component** column | Drives the build plan, the scaffold and the test summary |
| No record of where a requirement came from | **Source**: BRD row, transcript timestamp, design file, or `ASSUMPTION` | An AI-drafted criterion must be checkable against its source. An unsourced one is an assumption, and is labelled so |
| "NOTE: check if…" inside descriptions | **Open Questions** column | Questions get answered, not lost in a paragraph |
| "Alterations if any", undated | **Alterations (dated)**: `YYYY-MM-DD · who · what` | Change control after sign-off |
| No status | **Status**: Candidate / Draft → In Review → Approved → Changed, with On Hold and Out of Scope | The sign-off, `/deliver` and traceability need to know what is live |
| Type and priority implicit | **Type** and **Priority** (MoSCoW) with dropdowns | Test planning and scope negotiation |
| "Intranet Links" sheet for client-supplied content | **Client Inputs**: one row per thing the client owes, with status and the AC it serves | Tests blocked on the client show as *Blocked*, not *Fail* |
| One test sheet per screen, headers varying between sheets | **One Test Cases sheet**, fixed columns, filter by component | One shape to read and write. Feature and component are **looked up** from the AC ID, so a mistyped ID shows `⚠ Unknown AC ID` instead of silently pointing at the wrong feature |
| Summary typed by hand | **Summary** calculated by formula | It can't drift from the test sheet |
| "Key Links" including a credentials link | **References**, with a standing rule: no credentials | Workbooks get emailed |
| Accessibility, permissions and loading/error states written into (or cut from) each row | **Delivery Standards** sheet: one place, applying to every criterion, not scope to trade away | A reviewer who removes "technical" rows must not be able to remove how Acies builds |
| Questions in PROJECT.md or inside cells, invisible to the PO | **Questions** sheet: question, why it matters, **current baseline**, owner, status, answer | The PO answers where they review, and an unanswered question has a defined outcome |
| Every BRD row becomes a criterion, padded with assumptions | **Candidate** status for BRD-only items | The PO promotes what is wanted; the baseline holds only what the client showed or said |

## 2. Sheets and columns

**Acceptance Criteria:** AC ID · Screen Section · User Role · Feature · Description · Acceptance
Checks · Power Apps Component · Data (Lists & Fields) · Type · Priority · Source · Client Input Needed · Open
Questions · Status · Alterations (dated)

**Delivery Standards:** Standard ID (`STD-A11Y`) · Standard · Applies to · Checks · Basis

**Questions:** Q ID (`Q-12`) · AC IDs · Area · Question · Why it matters · Current baseline (built if
unanswered) · Owner · Status (Open / Answered / Closed) · Answer · date

**Client Inputs:** Input ID (`IN-01`) · AC ID · Item · Value / Link · Provided By · Status (Awaiting /
Received / Not Needed) · Notes

**Test Cases:** TC ID · AC ID · Check # · Feature *(formula)* · Power Apps Component *(formula)* · Test
Scenario · Type · Preconditions · Steps · Expected Result · Iteration · Status · Comments · Bug Ref

**Summary** *(formulas)* · **References** · **Read Me** (document control and the rules below)

## 3. IDs

- `AC-<PROJECT>-NN`, `TC-<AREA>-NNN`, `IN-NN`. `<PROJECT>` is the **project code** (PROJECT.md §1), and
  `NN` is one running number for the whole project, starting at `01` (`AC-CON-01`, `AC-CON-02`, …) and
  never restarting per screen. This is the format the testing team uses across projects: they map their
  test cases to these IDs and add the feature name from the **Feature** column. A check is cited
  `AC-CON-07.3`. A test case's AREA is a 2–6 letter code for the screen or module (`NAV`, `HOME`,
  `A11Y`, `SEC`) and is separate from the AC ID. `ac_workbook.py check` rejects an AC ID whose code is not
  the workbook's project code.
- **Permanent.** Never renumber, never reuse. A new criterion takes the next free number in the project,
  even if that leaves a gap. A criterion taken out of scope keeps its row with status *Out of Scope*. Rows are never deleted.

## 4. Writing a criterion

| Do | Don't |
|---|---|
| One feature per row; several checks per feature | Bundle layout, theming and links into one sentence |
| Each check is **observable**: someone can look or click and say pass/fail | "Should be user-friendly", "fast", "modern" |
| Put numbers in **when an input gives them**: counts in the design, limits the PO stated | "A few items", "a short time". Equally, a limit nobody gave, written as if the client chose it. Cite the design element, or state the number as a question's baseline |
| Cover what is **specific to the feature** at its limits (0 items, a missing link, long text). Generic loading, empty, error and permission behaviour is in Delivery Standards | Repeat the standards in every row, or describe only the happy path |
| Write a data fact the client stated as a **check**: "both read the same list", "the client keeps it up to date by hand, changes are rare" | Leave it in the Data column, where the PO doesn't look |
| When the speaker withdraws a statement or rules work out ("no sync", "ignore that"), drop the withdrawn content everywhere and write a **not-built** check | Leave the withdrawn statement in a note, or only in the coverage map |
| Say what happens at limits: zero items, maximum items, long text, missing link | |
| State what the user sees, in their words | Name implementation details (component props, REST calls) unless the client requires them |
| Name the list and its fields in the Data column | Leave the data model for developers to guess |
| Give the source. If nobody said it, write `ASSUMPTION — <why>` and add an Open Question | Present an inference as a requirement |

**Cross-cutting behaviour is not scope.** Accessibility (WCAG 2.1 AA, default D9), the loading, empty,
error and no-permission states (design standard §5) and permissions by list permissions (D6) live in the
**Delivery Standards** sheet. They apply to every criterion and are tested once per component, citing
`STD-A11Y`, `STD-STATES`, `STD-PERM`. A reviewer who cuts rows must not be able to cut them. Performance
and responsiveness targets are criteria only when an input states them; otherwise they are questions.

**Scope basis.** PROJECT.md §3 records what counts as scope. The default: a feature the accepted design
shows or the PO walkthrough describes is in; a feature only the BRD mentions is a `Candidate` until the PO
promotes it.

**Sources and decisions.** When the PO answers an assumption's question, the Source becomes `PO decision
YYYY-MM-DD (Q-nn)`; the check list and the Alterations line say what changed. `Client Input Needed` holds
IN-ids and `Open Questions` holds Q-ids; the detail lives on its own sheet.

## 5. Status and change control

| Status | Meaning | Who sets it |
|---|---|---|
| Candidate | Only the BRD mentions it. Not in the baseline until the PO promotes it | `/acceptance-criteria` |
| Draft | Written, not yet reviewed | `/acceptance-criteria` |
| In Review | With the PO | BA |
| Approved | Signed off. Live scope | PO (and the Read Me's *Approved by / on*) |
| Changed | Altered after approval. The *Alterations* line says what and who | BA, with PO agreement |
| On Hold | Agreed for later. Nothing is built, and the *Alterations* line says what is awaited | PO |
| Out of Scope | Dropped. The row stays for the record, and the *Alterations* line says who decided and why | PO |

Only `Approved` and `Changed` rows are built. The tool still reads the old names *Deferred* and *Removed*,
with a warning.

**One working copy.** The PO and BA edit the workbook in Excel, keeping its sheets, columns and
drop-downs. They don't regenerate it or keep a second copy; `uv run tools/ac_workbook.py diff <old> <new>`
lists what a review changed and reports deleted rows, dropped sheets and statuses outside the format. A
returned copy is merged by `/acceptance-criteria` §6a, never replaced and never overwritten.

After approval, Claude **never rewrites the workbook**. A changed input produces a list of proposed
alterations for the PO to accept. Accepted ones are entered as *Changed* rows with a dated
*Alterations* line, and `/status` reopens the downstream stages that depended on them.

## 6. Test cases

- One row per test case. It cites the AC **and the check number** it proves.
- At least one test per approved check that has behaviour. Add *Negative*, *Edge* or *Boundary* tests
  for every input, limit and failure the checks describe, and an *Accessibility* test per component.
- Steps are numbered and reproducible by someone who has never seen the project. Preconditions
  include the data needed (e.g. "an announcement with ExpiryDate yesterday").
- **Re-tests update the row in place**: Iteration +1, Status to the new result, and the earlier
  result moved into Comments (`It1: Fail — BUG-014. It2: Pass`). The summary then always shows the
  latest result.
- A test that can't run because the client owes something is *Blocked*, with the Input ID in Comments.

## 7. Traceability to code

The implementing formula carries the AC ID in a Power Fx comment, and the implementing flow step in its *Notes* (dev-standards §9). Then:

```
uv run tools/ac_workbook.py check specs/acceptance-criteria/<CODE>_AcceptanceCriteria.xlsx --src canvas --src solution/src
```

It reports: malformed or duplicate IDs, missing required cells, invalid dropdown values, assumptions
with no open question, test cases pointing at criteria that don't exist (or at a check number they
don't have), live criteria with no test, and live criteria with no reference in the app or flows.

## 8. Tool reference

| Command | Use |
|---|---|
| `build <data.json> <out.xlsx>` | Create the workbook from JSON (what `/acceptance-criteria` does). Refuses to overwrite without `--force` |
| `dump <xlsx> [--format md\|json] [--out FILE]` | Read the workbook back. **Downstream skills read this, never the .xlsx** |
| `append-tests <xlsx> <tests.json>` | Add test cases; keeps every other cell, skips existing IDs, refreshes the summary |
| `check <xlsx> [--src canvas --src solution/src]` | Validate, and trace into the app YAML and flows |
| `diff <old.xlsx\|old.json> <new.xlsx> [--out FILE]` | What a review changed, and what it lost |
