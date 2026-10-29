---
name: reset-template
description: Turns a delivered Power Apps project back into the clean Acies template (removes the client's canvas app, solution, lists, specs, inputs and settings; restores the starter app, solution and PROJECT.md; keeps tools, standards, traps and skills). Use when the user runs /reset-template or asks to clean the repo so it can be used as a template for the next project.
disable-model-invocation: true
---

# /reset-template

Use this when a project is finished and the repository should become the template again. It is destructive for the project's files, so
follow the order and never skip the dry run.

## 0. Before you start

- Everything must be committed (the script refuses otherwise). The project's history stays in git; say so to the user: they can still
  reach the delivered project through the commits and, if they want, a tag (`git tag delivered-<code> HEAD` first, ask).
- Ask **once** which, if any, project files they want to keep (for example the delivered solution ZIP, or the AC workbook as a sample).
  Anything kept is copied to a folder outside the repository first, never left in the template.
- The starter files come from the git tag `template-starter`. If the tag is missing, ask which commit holds the clean starter.

## 1. Dry run

`uv run tools/reset_template.py` lists what will be removed (the canvas app, `solution/src`, settings files, `dist/`, list CSVs, specs,
inputs, working folders), what is moved (the project's `tools/build_*.py` generators become `tools/examples/*.example.py`: worked
examples, delete them if the user does not want them) and what is restored from the starter. Show the user the list, then continue
only when they agree.

## 2. Apply

`uv run tools/reset_template.py --apply`, then:

1. `uv run tools/pp.py doctor` and `uv run tools/pp.py build`: 0 errors (the starter's one warning about the YAML-packed app is expected).
2. `uv run python -m unittest discover -s tools/tests` and `uv run tools/powerfx.py --selftest`: all pass.
3. **Prove the template still sets up a project:** copy the repository to a temporary folder (not inside it), run
   `uv run tools/pp.py setup --client Test --project Check --code TC` there, then `uv run tools/pp.py build`: 0 errors. Delete the copy.
4. Search for leftovers of the project's name, code and prefix in tracked files:
   `git grep -inE "<client>|<project>|<prefix>_"` outside `docs/lessons-learned.md`, `CHANGELOG.md` and `tools/examples/`. Fix what it finds.
5. `CHANGELOG.md`: replace the project's entries with one template entry that lists the tooling, standards and traps the project added
   (read them from the project entries before deleting). Keep the older template history below it.
6. `README.md` and `docs/`: anything that names the finished project must be generic again (examples may keep fictional names).
7. PROJECT.md must be the blank card (`Project code 🔶`, every stage `Not started`).

## 3. Finish

Show `git status`, suggest one commit (`Reset to the clean template`) and, if wanted, a tag `template-<version>`. Do not commit or tag
without being asked. Report what was removed, what was kept as an example, and the verification results.
