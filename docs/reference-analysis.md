# Reference solution analysis

What a real delivery's solution export (*EvidenceManagementSystem* 1.0.0.4, unmanaged) taught this
template. It was read for its **structure and packaging**; nothing client-specific was copied, and no
client names, tenant addresses or people appear here.

## 1. Structure of an exported solution

| Part | In the ZIP | In source (`pac solution unpack`) |
|---|---|---|
| Manifest: name, version, publisher, root components | `solution.xml` | `Other/Solution.xml` |
| Components' metadata | `customizations.xml` | `Other/Customizations.xml` (flows and apps moved to their own files) |
| Package parts | `[Content_Types].xml` | (regenerated) |
| Cloud flows | `Workflows/<Name>-<GUID>.json` + a `<Workflow>` entry in customizations | `.json` + `.json.data.xml` |
| Canvas app | `CanvasApps/<logical>_DocumentUri.msapp`, `_BackgroundImageUri` (PNG), `_AdditionalUris0_identity.json`, + a `<CanvasApp>` entry | `<logical>.meta.xml` + the same files |
| Environment variables | `environmentvariabledefinitions/<schema>/environmentvariabledefinition.xml` | same |
| Connection references | `<connectionreferences>` in customizations | same, in `Customizations.xml` |

Root components were the flows (type 29) and the app (type 300); variables and references travelled
as components of the package without root entries. The template follows the same shape.

The `.msapp` (Studio document format 1.349, structure 2.4.0) now carries `Src/*.pa.yaml` beside
Studio's compiled `Controls/*.json`. `pac canvas unpack --layout SourceCode` splits it into the YAML
and a `.msapr` archive of everything else.

## 2. Contents

| Component | Count |
|---|---|
| Canvas app | 1, 25 screens |
| Cloud flows | 21 (SharePoint item triggers, Power Apps triggers, manual buttons, one recurrence) |
| Environment variables | 32, all SharePoint data-source variables (a site and its lists) |
| Connection references | 10 across 5 connectors |

## 3. What it does well, and the template keeps

- Lists reached through **data-source environment variables**: a site variable, list variables as its
  children. The template's `SharePointSite` / `SampleList` pair is this pattern.
- Flows read those variables as parameters (`@parameters('Name (schema)')`) and use **connection
  references**, not embedded connections.
- No current values packaged: the export carried definitions only.

## 4. What it gets wrong, and the template prevents

Each became a trap ([powerapps-traps.md](standards/powerapps-traps.md)) and, where it can be detected, a `pp.py validate` check.
Run against the reference ZIP, `validate` reports 120 errors and 18 warnings.

| Finding | Trap | Template |
|---|---|---|
| Built in the environment's **default publisher** (`new_` prefix) | PA-T1 | Project publisher set by `setup`; `validate` fails a default publisher |
| A full second set of variables prefixed `TEST_` (15 of the 32) | PA-T2 | One variable, one value per environment in `deployment/` |
| 10 connection references for 5 connectors (4 for SharePoint), auto-named `…_ea9e2` | PA-T3 | One readable reference per connector; `validate` warns on duplicates |
| A premium connector (Azure Blob Storage) | D2, D3 | `allowedConnectors`; `validate` fails anything else |
| Flow parameters carrying the Dev site URL and list IDs as defaults | PA-T5 | `export` clears them; `validate` fails them |
| Hard-coded SharePoint site and drive IDs in flow steps | PA-T5 | Variables only; `validate` fails the `sites/<host>,<guid>,<guid>` form |
| Named users' email addresses hard-coded in `App.OnStart` for access | PA-T6, D6 | A list or group holds people; list permissions enforce access; `validate` fails emails in app YAML |
| Tenant URLs in screen formulas | PA-T5 | Variables only; `validate` fails tenant hosts in app YAML |
| A logo embedded with a signed storage URL in the app's resources | PA-T7 | Template's app has no embedded assets; repository kept private |
| A leftover test flow (`TEST2`) shipped | — | Review `git diff` after every `export` |
| Inline colour literals (`RGBA(42, 147, 48, 1)`) set as variables in `OnStart` | D11 | Named-formula tokens in `App.Formulas` |

## 5. How the template's canvas app was made

The template's `.msapr` keeps only Studio's generic scaffolding from the reference app: the document
header (format version), the default theme, the definitions of the control types it uses, and the
root App/Host control (`Controls/1.json`, with the client's `OnStart` removed; PA-T20). The app's properties were rewritten with new IDs; data sources, connection
references, resources, images, the app checker results and every screen were dropped. The screens are
new YAML. `pac canvas pack` accepts the result; Studio compiles it on first open (PA-T8).
