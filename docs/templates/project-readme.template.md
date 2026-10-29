<!-- tools/pp.py setup copies the two blocks below into README.md, replacing the template's own. -->

<!-- README:intro -->
# {Client} — {Project}

The Power Apps solution Acies Innovations is delivering for {Client}. Project code `{CODE}`, solution `{solution}`,
publisher prefix `{prefix}_`, canvas app *{app}*. Built from the Acies Power Apps delivery template: the version it
started from is the newest template entry in [CHANGELOG.md](CHANGELOG.md).

| Read | For |
|---|---|
| [PROJECT.md](PROJECT.md) | **Start here.** Who the client and PO are, where every stage stands, decisions, open questions, tenant facts, environments, what is reused |
| This file | Setting up your machine, creating lists, building, importing and deploying |
| [docs/pipeline.md](docs/pipeline.md) | How the stages fit together, the one sign-off, where Claude's work meets Studio |
| [PROMPTS.md](PROMPTS.md) | Every automation, how to run it, and the supporting prompts |
| [CLAUDE.md](CLAUDE.md) | The rules Claude works by in this repository |
| [specs/](specs/) | The signed-off acceptance criteria, design spec, build plan, data model, release notes |
| [releases/](releases/) | Every release candidate's solution ZIPs, ready to import |

---
<!-- /README:intro -->

<!-- README:start -->
## Joining this project

1. Clone the repository and install the [prerequisites](#prerequisites): `pac`, PowerShell 7, uv, the GitHub CLI.
2. From the repository root: `uv sync` ([Setting up the Python tools](#setting-up-the-python-tools)), then
   `uv run tools/pp.py doctor` and `uv run tools/pp.py build`: 0 errors.
3. `pac auth create --environment <Dev URL from PROJECT.md §6.1>`, only if you will import or export.
4. The client's inputs are already in `inputs/`, with their text in `inputs/_converted/`. If a new version arrives,
   add it there and run `/ingest`; never edit a file in place.
5. Check you can read the [reuse catalogue](#the-reuse-catalogue): `uv run tools/catalogue.py fetch`.
6. Run `/status` in Claude Code: it shows every stage, what is blocking, and what to do next.
7. To work on the app in Studio, open it **from the imported solution** in Dev, never as a loose `.msapp`
   (PA-T8, PA-T26), then **Run OnStart** once.

The stages, and the skill that runs each one:

| Stage | Skill | Produces |
|---|---|---|
| G0 | `/project-setup` | PROJECT.md, the named solution |
| G1 | `/ingest` | `inputs/_converted/`, `specs/prototype-fidelity.md` |
| G2 | `/acceptance-criteria` | `specs/acceptance-criteria/{CODE}_AcceptanceCriteria.xlsx`. **The Client PO signs it off: the only approval** |
| G3–G11 | `/deliver` | Design spec, build plan, list schemas, screens, formulas, flows, test cases, release candidate in `releases/` |
<!-- /README:start -->
