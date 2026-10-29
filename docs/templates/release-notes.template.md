# {Client} {Project} — release {version}

> Written by `/verify release` for the delivery lead (stage **G11**). Also the hand-over note for whoever
> imports it.

| | |
|---|---|
| Packages | `dist/{Solution}_{v}_managed.zip` ({size} KB) · `dist/{Solution}_{v}.zip` (unmanaged, Dev only) |
| Version | {x.y.z.w} |
| Built | {date}, from commit {sha} |
| `pp.py build` (validation) | ✅ 0 errors · warnings: … |
| `check_schemas.py` | ✅ |
| `ac_workbook.py check --src canvas --src solution/src` | {n} live criteria, {n} traced, {n} with tests |
| Solution checker (`pp.py check`) | {result, or "not run: needs pac auth"} |
| Tests (latest iteration) | {passed} pass · {failed} fail · {blocked} blocked · {notrun} not run |

## What's in it

| Piece | Kind | AC IDs |
|---|---|---|

## Changes since the last release

## Known issues

Failing or blocked tests, warnings `pp.py build` reported, and anything shipped with a 🔶.

## Deploying

1. **Lists** on {site}: `uv run tools/check_schemas.py`, then `schemas/import-lists.console.js` (README
   **Creating the lists**). New or changed lists: …
2. **Import** the managed ZIP in the portal: Solutions → Import solution → Browse → Next → Next.
3. **In the wizard**, bind the connection references ({list}) and set the environment variables:
   site = {site URL}, {list variables}, {text values}. (Scripted import with settings files is optional.)
4. **After import**: turn the flows on. **First import of this app version**: open the app in Studio, **Save**, **Publish** (PA-T8). If a
   list is new: add it as a data source in Dev first (PA-T13), export, rebuild.
5. **Share** the app with {groups}; add run-only users to app-called flows.
6. **Smoke test**: …
7. Record the release in PROJECT.md §7.
