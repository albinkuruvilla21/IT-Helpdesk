# specs/

What the pipeline produces. Each file is the record for its stage in `PROJECT.md` §2. The AC workbook
is the one the client signs off; `/deliver` writes the rest.

| File | Stage | Written by | Template |
|---|---|---|---|
| `acceptance-criteria/<CODE>_AcceptanceCriteria.xlsx` | G2, G10 | `/acceptance-criteria`, `/test-cases` (via `tools/ac_workbook.py`) | [sample](../samples/acceptance-criteria/) |
| `acceptance-criteria/coverage.md` | G2 | `/acceptance-criteria`: every BRD requirement → AC IDs | |
| `acceptance-criteria/proposed-changes-<date>.md` | after G2 | `/acceptance-criteria` when inputs change after sign-off | |
| `prototype-fidelity.md` | G1, G2, G7, G8 | `/ingest` (inventory), `/acceptance-criteria` (AC IDs), `/ui-dev` and `/functionality-dev` (built as, status) | [template](../docs/templates/prototype-fidelity.template.md) |
| `design-spec.md` | G3 | `/design-spec` | [template](../docs/templates/design-spec.template.md) |
| `build-plan.md` | G4 | `/build-plan` | [template](../docs/templates/build-plan.template.md) |
| `data-model.md` | G5, G9 | `/list-schemas`, `/flows` | [template](../docs/templates/data-model.template.md) |
| `release-notes.md` | G11 | `/verify release` | [template](../docs/templates/release-notes.template.md) |

`_working/` folders hold intermediate files (JSON the workbook is built from, generator scripts). They
are git-ignored and are never the record.

**The AC workbook is edited in Excel by people** (PO sign-off, tester results, alterations). Claude
creates it and appends test cases through the tool, and otherwise only reads it.
