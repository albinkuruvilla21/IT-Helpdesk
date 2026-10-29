# samples/

Exemplars: what a good artefact looks like. Skills copy their **shape**, never their content. Every
sample is fictional (Contoso) or generic. None of it is real client data, and none of it is deployed.

| Sample | Shows | Used by |
|---|---|---|
| `acceptance-criteria/Sample_AcceptanceCriteria.xlsx` | The AC workbook for a fictional *Site Requests* app: every sheet, column, dropdown and formula, the *Power Apps Component* naming (`<App>: scr<Name>`, `Flow: <name>`), a Candidate row, an answered question | `/acceptance-criteria`, `/test-cases`, people learning the format |
| `acceptance-criteria/Sample_AcceptanceCriteria.json` | The JSON that workbook is built from (`tools/ac_workbook.py build`): the shape Claude writes | `/acceptance-criteria` |
| `schemas/SAMPLE_Announcement.csv` | A list schema that passes every rule | `/list-schemas` |
| `schemas/_reference/` | SharePoint's raw "list from CSV" export, which shows the format but **fails our rules** (a currency with no code). Field XML syntax only | — |
| `powerapp/` (`*.msapp` and `Src/`) | **A Studio-built canvas app: the UI reference** (a request-and-approval app built by hand from a client prototype, so its wording is that project's). Its layout is proven in Studio. `docs/standards/ui-patterns.md` documents its patterns, `tools/canvas_ui.py` encodes them (`--selftest` rebuilds parts of it and compares), and `tools/examples/clone_reference_app.example.py` is the worked example of cloning it into a project. For another project, put that project's Studio-built app here | `/scaffold`, `/ui-dev`, `/design-spec` |
| `flows/SAMPLE-NotifyOnNewItem.json` (+ `.json.data.xml`) | A solution flow: SharePoint trigger on variable-driven site and list, Try/Catch, connection references, AC ID in a step's notes. The same as the starter's flow, kept here after `/scaffold` removes it from the solution | `/flows` |

The sample workbook's `AC-CON-01`, `AC-CON-02` and `AC-CON-06` describe the starter app's home
screen and the starter flow, so
`uv run tools/ac_workbook.py check samples/acceptance-criteria/Sample_AcceptanceCriteria.xlsx --src canvas --src solution/src`
shows traceability working on a fresh copy of the template.

To rebuild the sample workbook after changing the tool or the JSON:
`uv run tools/ac_workbook.py build samples/acceptance-criteria/Sample_AcceptanceCriteria.json samples/acceptance-criteria/Sample_AcceptanceCriteria.xlsx --force`
