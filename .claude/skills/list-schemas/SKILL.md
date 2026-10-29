---
name: list-schemas
description: Stage G5. Writes one SharePoint list schema CSV per list in the build plan (schemas/<PREFIX>_<Entity>.csv, in the import-lists format) plus specs/data-model.md, adds each list's data-source environment variable to the solution and the deployment settings, and validates them. Use when the user runs /list-schemas or asks to create the list schemas.
disable-model-invocation: true
---

# /list-schemas: stage G5

Internal names and field IDs become **permanent** the moment a list is created. Get them right here.

## 0. Before you start

`PROJECT.md` §2: **G4 must be `Done`.**

If `schemas/` already holds a CSV for a list, you are **changing** it: keep every existing field's
`Name` and `ID` exactly, and only append fields (list-schema-standard §4). Never regenerate an existing
field's GUID.

## 1. Read

`docs/standards/list-schema-standard.md` (all of it) · `samples/schemas/SAMPLE_Announcement.csv` (the
exemplar: copy its format exactly) · `specs/build-plan.md` §2, §1 and §3 (which screens and flows read
and write each list, and how) · the AC dump (each row's *Data* column and checks: they tell you the
filters, sorts, limits and choice values) · `docs/templates/data-model.template.md` · `PROJECT.md` (list
prefix; §3 for single-currency decisions).

## 2. Design each list

| Column | Rule |
|---|---|
| `Title` | SharePoint's base field, copied **verbatim** from the exemplar's first field. Decide what it holds (the item's name or headline) |
| Fields from the AC | PascalCase internal names; prefix generic ones (`LinkStyle`, not `Style`; `RequestSummary`, not `Description`) |
| References to other lists | `<Target>Id` (`Number`, `Decimals="0"`, `Min="1"`, indexed: the target's item ID) + `<Target>Title` display value. **Never a Lookup**, and no GUID identity column (dev-standards L2, L3) |
| People | A Text column for the email (`RequesterEmail`, indexed when filtered) and one for the display name. Filters on Person columns don't delegate to SharePoint (PA-T14) |
| A document library, or columns on a list SharePoint already has | `"baseTemplate": 101` or `"existingList": "…"` in line 1 (list-schema-standard §1); no sample rows |
| Money | `Currency` with `LCID`, plus `<Name>CurrencyCode` (Text), unless single-currency is recorded |
| Ordering / visibility the design implies | `SortOrder` (Number), `IsActive` (Boolean), `PublishDate` (DateTime) |
| Indexes | Every field any screen or flow will filter or sort by. Read the AC checks for "newest first", "active", "mine", "pending". Then add each list's default-view filter |

Choice values come from the AC. A value the AC doesn't settle → 🔶 in data-model.md and an open question.

## 3. Generate the CSVs with a script

Write a small Python script in `specs/_working/` (git-ignored) that builds each CSV the way the
exemplar is built: line 1 `ListSchema=` + `json.dumps({"schemaXmlList": [...]})`, line 2 the quoted
display-name header, then ≤ 5 sample rows (`csv.QUOTE_ALL`). New field IDs from `uuid.uuid4()`. Sample
rows: illustrative only, `example.com` addresses and links, no real names; a `<Target>Id` holds the
target's row number in its own CSV. Hand-writing escaped XML-in-JSON produces broken files.

## 4. Add each list to the solution

For every list, an environment variable definition in
`solution/src/environmentvariabledefinitions/<prefix>_<Entity>List/environmentvariabledefinition.xml`,
shaped exactly like the starter's `acies_SampleList` (now `<prefix>_SampleList`): data source type
`100000004`, `apiid` SharePoint, `parameterkey` `table`, `parentdefinitionid` the site variable
(`<prefix>_SharePointSite`), display name "<Entity> list". No value files (PA-T4).

Then `uv run tools/pp.py build`. Update PROJECT.md §6.2. The person importing the ZIP chooses the site
and list in the import wizard, so nothing else is needed. (Only if the project uses settings files for
scripted imports: add each new variable to them, empty.)

## 5. Check

- `uv run tools/check_schemas.py`: **0 errors**. Resolve every warning or justify it in data-model.md.
- `uv run tools/pp.py build`: 0 errors.

## 6. Write `specs/data-model.md`

From the template: per list, purpose, site, volume, **threshold strategy**, **archival policy**,
**permissions** (list-level; who edits), the environment variable, the column table and AC IDs. Then
relationships and the flows table (filled in by `/flows`). An archival policy may be "none needed", with
the reason. It may not be blank.

## 7. Finish

- PROJECT.md G5 → `Done`.
- Reply with: the lists and their column counts, indexes and why, permissions, the variables added, any
  🔶, and how to create the lists on the dev site: the README's **Creating the lists** section
  (`schemas/import-lists.console.js`).
