---
name: flows
description: Stage G9. Writes the Power Automate cloud flows in the build plan as solution components (solution/src/Workflows/<Name>-<GUID>.json + .json.data.xml), using connection references and environment variables only, standard connectors only, and records them in the data model. Use when the user runs /flows.
disable-model-invocation: true
---

# /flows: stage G9

## 0. Before you start

`PROJECT.md` §2: **G5 must be `Done`.** If build-plan §5 lists no flows, set G9 → `Done` ("no flows"),
say so, and stop.

## 1. Read

`docs/standards/flow-standard.md` · `samples/flows/` (both files; copy the shape) · `specs/build-plan.md`
§5, §3 and §1.1 (any flow it starts from, in `references/`) · `specs/data-model.md` · the CSVs for every list a flow touches · the AC rows each flow
implements · `solution/src/Other/Customizations.xml` (the connection references) and
`solution/src/environmentvariabledefinitions/` (the variables).

## 2. For each flow

1. Choose the trigger (flow-standard §3): a SharePoint item trigger (create-only if the flow writes back
   to that item, T-22), a schedule, or *PowerAppV2* if the app calls it. **Never** an HTTP request
   trigger or HTTP action (premium).
2. New GUID: `uv run python -c "import uuid;print(uuid.uuid4())"`. Name: the display name without spaces.
3. Write `solution/src/Workflows/<Name>-<GUID upper>.json`:
   - `properties.connectionReferences`: one entry per connector, `connection.connectionReferenceLogicalName`
     = a reference in `Customizations.xml` (add one there, in PROJECT.md §6.3 (and in the settings files, if the project uses them), if
     the connector has none yet).
   - `definition.parameters`: `$connections`, `$authentication`, and one parameter per environment
     variable used, named `"<Display name> (<schema>)"`, `defaultValue` `""`, `metadata.schemaName`.
     Add a text variable if the flow needs a value no variable holds yet.
   - Steps renamed to say what they do; `Try` and `Catch` scopes; the AC ID with check number in each
     implementing step's `"description"`.
4. Write `<Name>-<GUID upper>.json.data.xml`: copy the sample's, with the GUID (lower case, braces),
   the file name and the display name. `StateCode 0`, `StatusCode 1` (imports off).
5. Add `<RootComponent type="29" id="{<guid>}" behavior="0" />` to `Other/Solution.xml`.
6. Make every step safe to re-run, and order writes so a failure part-way never leaves a state the app
   reads as complete (flow-standard P8).

## 3. Check

- `uv run tools/pp.py build`: 0 errors. It checks JSON, references, variables, connectors, HTTP, values
  and hard-coded data for every flow.
- If the project uses settings files: `uv run tools/pp.py settings`: every new variable and reference present in each.
- Every `$filter` field is indexed in its CSV.
- A flow the app calls: `uv run tools/pp.py fx` checks every `'<Flow name>'.Run(…)` against this flow's display name and its
  Power Apps (V2) trigger inputs (`FX-FLOW`, powerfx-validation §3). Renaming a flow or changing its inputs means changing the app's
  calls in the same session.

## 4. Finish

- Fill the flows table in `specs/data-model.md` §3 (owner, trigger, failure behaviour, *Verified on
  tenant: no*).
- PROJECT.md G9 → `Done`. Reply with the flows, their triggers, and what someone must do after import:
  bind the references and set the variables in the import wizard, turn each flow on, run it once,
  and record it as verified.
