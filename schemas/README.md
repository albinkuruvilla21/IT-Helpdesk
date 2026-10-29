# schemas/

One CSV per SharePoint list the app uses, named exactly after the list (`CON_SiteRequest.csv`), plus the
importer.

| File | |
|---|---|
| `<PREFIX>_<Entity>.csv` | Written by `/list-schemas`. Format and rules: [list-schema-standard.md](../docs/standards/list-schema-standard.md) |
| `import-lists.console.js` | Creates the lists on a site from this folder. Paste it into the browser console: steps in the [README](../README.md#creating-the-lists) |

Before importing anywhere: `uv run tools/check_schemas.py` must report **0 errors**.

A CSV is changed by **appending** fields, never by renaming an internal name or regenerating a field ID.
Change `specs/data-model.md` in the same commit. Each list also has a data-source environment variable
in the solution (`solution/src/environmentvariabledefinitions/`), so the app and flows find it in every
environment.

The format exemplar is [samples/schemas/SAMPLE_Announcement.csv](../samples/schemas/SAMPLE_Announcement.csv).
