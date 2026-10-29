# Power Automate flow standard

Flows are for **notification, scheduled housekeeping, approvals and light glue** between lists, and for
actions the app needs a connector for. Rules a user waits on that the app can do belong in the app;
anything long-running or privileged needs a conversation first.

Exemplar: [samples/flows/](../../samples/flows/) (the starter's flow, which `/scaffold` removes from the
solution).

## 1. Files

Unlike the SPFx template, a flow here is a **real solution component**: it is packaged in the ZIP,
imported with the app, and bound to the environment through connection references and environment
variables. Each flow is two files in `solution/src/Workflows/`:

| File | Holds |
|---|---|
| `<Name>-<GUID>.json` | The definition: `properties.connectionReferences` (each pointing at a connection reference in the solution), `properties.definition` (parameters, triggers, actions) |
| `<Name>-<GUID>.json.data.xml` | The metadata: `WorkflowId` (the GUID, lowercase in braces), display name, `Category 5` (modern flow), `StateCode 0` (imports off) |

and one `RootComponent type="29"` line in `Other/Solution.xml`. `<Name>` is the display name without
spaces; the GUID is new (`uv run python -c "import uuid;print(uuid.uuid4())"`), upper-case in the file name.
A flow built in the designer arrives the same way through `pp.py export`.

## 2. Rules

| # | Rule | Why |
|---|---|---|
| P1 | **Standard connectors only.** No `When an HTTP request is received` trigger, no HTTP action, no premium or custom connector. `pp.py validate` enforces `allowedConnectors` | Premium licensing nobody budgeted for (T-25) |
| P2 | **Connections only through connection references** in the solution, one per connector (`<prefix>_<connector>`) | Bound per environment at import (PA-T3) |
| P3 | **Every environment value is an environment variable**, read as a parameter: `"Site request list (con_SiteRequestList)": {"defaultValue": "", "type": "String", "metadata": {"schemaName": "con_SiteRequestList"}}`, used as `@parameters('Site request list (con_SiteRequestList)')`. Defaults stay empty | The same solution runs in Dev, Test and Prod (PA-T5) |
| P4 | No secrets, ever | D7 |
| P5 | Runs under the **service account's** connections in Test and Prod; Power Apps-triggered flows decide per connection whether the caller's own identity is used | People leave; their flows stop (PA-T9) |
| P6 | A flow that **modifies the item that triggered it** uses a create-only trigger (`GetOnNewItems`) or a trigger condition | A "created or modified" trigger loops on its own write (T-22) |
| P7 | Every `$filter` field is indexed on the list | T-9 |
| P8 | **A failure never leaves data half-written in a state the app reads as complete.** Create the new before deleting the old; make every step safe to re-run. A flow that adds a row first looks for it by a deterministic key in an indexed Text column (`SourceKey = submitted:<item ID>`) | Retries and re-runs happen |
| P9 | **Try / Catch**: the work in a `Try` scope; a `Catch` scope running after *Failed* or *Timed out* that reports and ends with *Terminate: Failed* | Failures are visible in run history and to whoever supports it |
| P10 | Owner, trigger, connections and failure behaviour are recorded in `specs/data-model.md`'s flows table | Someone supports it after go-live |
| P11 | Every step implementing an acceptance check cites the AC ID in its *Notes* (`"description"`) | Traceability (`ac_workbook.py check --src solution/src`) |
| P12 | Flows import **off** (`StateCode 0`); a person turns them on once the variables are set (or `pp.py import --activate`) | Nothing fires against unset values (PA-T9) |

## 3. Shapes

| Trigger | JSON |
|---|---|
| SharePoint item created | `"type": "OpenApiConnection"`, `host.operationId: "GetOnNewItems"`, `parameters.dataset` / `table` from the site and list variables, `recurrence` (polling), `splitOn: "@triggerOutputs()?['body/value']"` |
| Schedule | `"type": "Recurrence"`, `recurrence: {frequency, interval, timeZone}` |
| Called from the app | `"type": "Request"`, `"kind": "PowerAppV2"`, `inputs.schema` with the parameters; reply with a `Response` action of kind `PowerApp` if the app needs a result |
| Button / manual | `"type": "Request"`, `"kind": "Button"` |

`samples/flows/SAMPLE-NotifyOnNewItem.json` is a complete example (SharePoint trigger, Try/Catch,
Outlook action, three variables, two references). Copy its shape.

## 4. Check

`uv run tools/pp.py build` validates every flow: JSON parses; every connection is a reference in the
solution; every connector is allowed; no HTTP; every `parameters('X')` is declared; every variable
exists; no values, tenant URLs, emails or site IDs. Then, on a tenant: import, bind, turn on, run
once, and record *Verified on tenant* in `specs/data-model.md` §3.
