# List schema standard

Microsoft Lists are the database. Every list is defined by **one CSV in `schemas/`**, named exactly
after the list, in SharePoint's "create list from CSV" format extended with explicit field XML.
`schemas/import-lists.console.js` creates lists from these files. `tools/check_schemas.py` checks them.

Internal names and field IDs are **permanent once a list exists**. Every rule below exists because the
alternative is a data migration.

## 1. File format

| Line | Contents |
|---|---|
| 1 | `ListSchema={"schemaXmlList":[ … ]}`: one JSON array of escaped `<Field/>` XML strings |
| 2 | Quoted CSV header row: the fields' display names, in order |
| 3–7 | Up to 5 illustrative sample rows. **Never real client data**: use `example.com` addresses and made-up names |

Exemplar: [samples/schemas/SAMPLE_Announcement.csv](../../samples/schemas/SAMPLE_Announcement.csv),
which passes every check. [samples/schemas/_reference/](../../samples/schemas/_reference/) holds the raw
SharePoint export it was modelled on, which shows SharePoint's format but **fails our rules** (a
currency with no code). Read it for field XML syntax only.

**Libraries and lists SharePoint already has.** Line 1's JSON may carry two optional keys next to
`schemaXmlList`:

| Key | Use |
|---|---|
| `"baseTemplate": 101` | Create a **document library** instead of a list (default 100). Library items need a file, so no sample rows |
| `"existingList": "Site Pages"` | Add the fields to a list SharePoint provides (news posts live in Site Pages) and never create one. The importer stops if the list is missing. No sample rows |

### Field anatomy

```xml
<Field DisplayName="Publish Date" Name="PublishDate" StaticName="PublishDate" Title="Publish Date"
       Type="DateTime" Format="DateTime" Indexed="TRUE" Required="TRUE" IsModern="TRUE"
       ID="{25191351-98ea-43e2-bdde-93a0d9a549c0}"
       Description="Indexed: the app filters and sorts on it." />
```

| Attribute | Rule |
|---|---|
| `Name` = `StaticName` | Set explicitly and identically. This is the internal name: PascalCase letters and digits, ≤ 32 characters |
| `DisplayName` / `Title` | Friendly, may contain spaces. Can change later; the internal name cannot |
| `ID` | A fresh `{GUID}` chosen when the field is first written, **never regenerated**. A new GUID makes a different column |
| `Indexed="TRUE"` | On every field a view or query filters or sorts by |
| `Description` | Say why the column exists, and why it is indexed |

The **first field is always SharePoint's base `Title` field, copied verbatim** from the exemplar
(`FromBaseType="TRUE"`): it is inherited, not created.

## 2. Rules

| # | Rule | Checked by `check_schemas.py` |
|---|---|---|
| S1 | File and list named `<PREFIX>_<Entity>`; prefix from PROJECT.md | ✅ |
| S2 | No identity column: an item is identified by its SharePoint ID (dev-standards L2) | ✅ (references, S6) |
| S3 | `Name` = `StaticName`, letters/digits only, ≤ 32 chars | ✅ |
| S4 | No reserved or generic internal names (`Type`, `Description`, `DisplayName`, `Name`, `URL`…): prefix them | ✅ |
| S5 | Field IDs unique across every schema in the project | ✅ |
| S6 | **No Lookup columns.** A reference is `<Target>Id`: `Type="Number"`, `Decimals="0"`, `Indexed="TRUE"`, holding the target's item ID, plus a `<Target>Title` display value | ✅ |
| S7 | Choice columns list their `<CHOICES>`; the code reads them from the column, never a hardcoded union | ✅ (presence) |
| S8 | Money: `Type="Currency"` with an `LCID`, paired with a `<Name>CurrencyCode` Text column, unless PROJECT.md records the project as single-currency | ⚠️ warning |
| S9 | ≤ 5 sample rows, illustrative only | ✅ / ⚠️ on real-looking emails and URLs |
| S10 | Every field a default view or query filters or sorts by is indexed (T-1, T-9) | ❌ by review: cross-check against the repositories' `$filter`/`orderBy` |
| S11 | `specs/data-model.md` states each list's purpose, volume, threshold strategy, archival policy and permissions | ❌ by review |

## 3. Choosing a type

| Need | Type | Note |
|---|---|---|
| Short text, codes, UPNs | `Text` | `MaxLength` 255 max |
| Reference to another list's item | `Number` named `<Target>Id` | `Decimals="0"`, `Min="1"`, `Indexed="TRUE"` (S6) |
| Long text | `Note` | `RichText="FALSE"` unless the design needs formatting. **Cannot be filtered server-side** (T-10) |
| Fixed set of values | `Choice` | Closed set at creation (T-11) |
| Number | `Number` | |
| Money | `Currency` + `…CurrencyCode` (`Text`, ISO 4217) | S8 |
| Date | `DateTime`, `Format="DateOnly"` or `"DateTime"` | Stored UTC |
| Yes/no | `Boolean` with `<Default>0</Default>` | |
| Link | `URL`, `Format="Hyperlink"` or `"Image"` | |
| Person | `User` | The importer won't import sample values for it. If code filters by person, also store the UPN in an indexed `Text` column |
| Image file | `URL` (`Format="Image"`) pointing at a library item, or a document library | Not attachments: they can't be indexed or listed cheaply |

## 4. Changing a schema after go-live

- **Add** columns freely, with new GUIDs.
- **Never rename an internal name** or reuse a field ID. Change the `DisplayName` instead.
- **Retire** a column by leaving it in place, removing it from views and code, and noting it in
  `specs/data-model.md`. Deleting loses data and breaks old versions of the package still cached in
  browsers.
- A new Choice value: add it on the live column **and** in the CSV, in the same change.

## 5. Importing

The steps are in the [README](../../README.md#creating-the-lists). The importer is safe to re-run. It
skips lists and fields that exist, and adds sample rows only to a list that is empty, so running it again
after adding a column adds just that column. A reference in a sample row (`<Target>Id`) holds the target's row
number in its own CSV, which is its item ID only in a list the importer has just created: SharePoint never
reuses an ID, even after a delete.
