---
name: project-setup
description: Stage G0. Turns a fresh copy of the Acies Power Apps template into a named project (solution, publisher prefix, app name, new IDs, PROJECT.md), checks the toolchain, and builds the starter solution ZIP. Use when the user runs /project-setup or asks to set up / initialise a new Power Apps project from the template.
argument-hint: "[client] [project] [code]"
disable-model-invocation: true
---

# /project-setup: stage G0

You are setting up a new Power Apps delivery project from the Acies template. Read `CLAUDE.md` and
`PROJECT.md` first.

## 1. Gather

You need: **client name**, **project name**, **project code** (2–6 letters, e.g. `CON`), the
**publisher prefix** (2–8 lowercase letters; defaults to the code), the **list prefix** (defaults to the
code), the **app's display name** (defaults to the project), whose **publisher** it is (Acies' or the
client's: PROJECT.md D-01), and optionally the **Dev environment URL** and **dev SharePoint site**. Take
them from `$ARGUMENTS`. Ask for anything missing, in one question. Don't invent a client name or code.

Say plainly before running: **the publisher prefix is permanent** once anything is imported (PA-T1).

If `PROJECT.md` already shows a project code, the project is already set up. Say so and stop, unless
the user explicitly asks to redo it (then pass `--force`, after warning that it renames every component
and orphans anything already imported).

## 2. Check the toolchain

| Check | Command | If it fails |
|---|---|---|
| uv | `uv --version` | Stop. Point the user to README *Setting up the Python tools*. uv brings the right Python and the tool packages into the repository's own `.venv`, so it never changes their Python |
| Tool packages | `uv sync`, from the repository root | `No pyproject.toml found`: the shell is outside the repository; `cd` to its root. Otherwise usually a network or proxy problem reaching PyPI |
| Chromium | `uv run playwright install chromium`, from the repository root | Report the error. Only `visual_compare.py` (G3, G7) needs it; the rest of the pipeline carries on |
| Toolchain | `uv run tools/pp.py doctor` | Stop on a failure. `pac` missing: show `dotnet tool install --global Microsoft.PowerApps.CLI.Tool` and ask before running it |

## 3. Set up

1. `uv run tools/pp.py setup --client "<client>" --project "<project>" --code <CODE> [--prefix <prefix>] [--list-prefix <PREFIX>] [--app-name "<App>"] [--publisher-name <Name> --publisher-display "<Name>"] [--dev-env <url>] [--dev-site <url>]`
2. `uv run tools/pp.py build`: 0 errors. One warning is expected (the YAML-packed app, PA-T8). Any
   error means the template is broken: report the output; don't patch around it.
3. Ask the user for the rest of PROJECT.md §1 (Product Owner, delivery lead, production site), §5 tenant
   facts and §6.1 environments. **Write 🔶 for anything they don't know.** Never fill a tenant fact with
   a likely guess.
4. **Reuse catalogue:** `uv run tools/catalogue.py fetch` (see `.claude/skills/catalogue/SKILL.md`). If it
   fails, report the message (read access to the catalogue repository; `gh auth setup-git`) and carry on.
   Then ask whether the user knows of an existing screen, flow or generator this project could reuse that
   **isn't** in the catalogue: record each in PROJECT.md §8 (repository link @ commit, path; *Rights* `Acies-owned` unless the user
   says a contract gives that code to a client). Also ask whether the contract gives the client the code
   (PROJECT.md §1 *Code ownership*: if nobody says so, it stays Acies). None is a fine answer. Matching the
   catalogue against the project's needs happens at `/ingest` and `/build-plan`; don't list its entries here.

## 4. Finish

- Set G0's Status to `Done` in PROJECT.md §2.
- Reply with: the solution, publisher and prefixes; the ZIP built; what is still 🔶; and the next step:
  put the BRD, transcript, accepted design/prototype and brand guidelines into `inputs/` (see
  `inputs/README.md`), then run `/ingest`.
- Mention that the starter ZIP can be imported into the Dev environment now to prove the environment
  works (README **Importing**), and that the starter app must be opened in Studio once (PA-T8).
- Commit: `G0: project set up` (CLAUDE.md §10: commit after every stage).
