#!/usr/bin/env python3
"""
Check every list schema CSV against docs/standards/list-schema-standard.md before it goes near a tenant.
Internal names and field IDs are permanent once a list exists, so a mistake caught here is a mistake
that never has to be lived with.

  uv run tools/check_schemas.py                 checks schemas/*.csv, prefix read from PROJECT.md
  uv run tools/check_schemas.py --prefix CON    explicit list prefix
  uv run tools/check_schemas.py path/to/dir     another folder (e.g. samples/schemas)

Exit code 1 if anything is an ERROR. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# SharePoint's own internal names, plus generic names that have failed on real projects: `Type` cannot
# be created, `Description` collides, and `DisplayName` creates fine then breaks every query that
# selects it (docs/standards/sharepoint-traps.md, T-4/T-5). Prefixing costs nothing; a collision is permanent.
RESERVED = {
    "ID", "Title", "Created", "Modified", "Author", "Editor", "Attachments", "ContentType", "ContentTypeId",
    "Type", "Description", "DisplayName", "Name", "URL", "Version", "Order", "GUID", "UniqueId",
    "FileRef", "FileLeafRef", "FileDirRef", "FSObjType", "ItemChildCount", "FolderChildCount",
    "AppAuthor", "AppEditor", "ComplianceAssetId", "Edit", "LinkTitle", "LinkTitleNoMenu", "DocIcon",
    "WorkflowVersion", "owshiddenversion",
}
INTERNAL_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,31}$")
GUID = re.compile(r"^\{[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}$")
EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.)+[\w-]+")
URL = re.compile(r"https?://([^/\s\"']+)", re.I)
SAFE_DOMAINS = ("example.com", "example.org", "example.net", "contoso.com", "fabrikam.com", "{tenant}", "tenant.sharepoint.com")
MAX_SAMPLE_ROWS = 5


def project_prefix() -> str | None:
    project = ROOT / "PROJECT.md"
    if not project.exists():
        return None
    m = re.search(r"^\|\s*List prefix\s*\|\s*`?([A-Za-z0-9]*)`?\s*\|", project.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m and m.group(1) else None


def check_file(path: Path, prefix: str | None, seen_ids: dict[str, str], errors: list, warnings: list):
    name = path.stem
    E = lambda msg: errors.append(f"{path.name}: {msg}")  # noqa: E731
    W = lambda msg: warnings.append(f"{path.name}: {msg}")  # noqa: E731

    if prefix and not name.startswith(prefix + "_"):
        E(f"list name must start with '{prefix}_' (the project's list prefix)")
    if not re.match(r"^[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+$", name):
        E("file name must be the list name: PREFIX_Entity, letters/digits/underscores, no spaces")

    text = path.read_text(encoding="utf-8-sig")
    first, _, rest = text.partition("\n")
    if not first.startswith("ListSchema="):
        E("line 1 must start with ListSchema=")
        return
    try:
        schema = json.loads(first[len("ListSchema="):].strip())
        xml_list = schema["schemaXmlList"]
    except (ValueError, KeyError) as e:
        E(f"line 1 is not valid ListSchema JSON ({e})")
        return
    # Optional keys: "baseTemplate" (100 list, the default; 101 document library) and "existingList"
    # (add fields to a list SharePoint provides, such as "Site Pages", instead of creating one).
    base_template = schema.get("baseTemplate", 100)
    existing = schema.get("existingList")
    if base_template not in (100, 101):
        E(f"baseTemplate must be 100 (list) or 101 (document library), not {base_template}")
    if existing is not None and not (isinstance(existing, str) and existing.strip()):
        E("existingList must be the title of a list that already exists, e.g. \"Site Pages\"")

    fields = []
    for xml in xml_list:
        try:
            el = ET.fromstring(xml)
        except ET.ParseError as e:
            E(f"unparseable field XML ({e}): {xml[:80]}")
            continue
        fields.append(el)

    if not fields or fields[0].get("Name") != "Title" or fields[0].get("FromBaseType") != "TRUE":
        E("the first field must be SharePoint's base Title field, copied verbatim from the reference CSV")

    names = {}
    for el in fields:
        a = el.get
        fname = a("Name") or ""
        base = a("FromBaseType") == "TRUE" or a("Type") == "Computed" or a("ReadOnly") == "TRUE"
        if base:
            continue
        where = fname or a("DisplayName") or "(unnamed field)"
        if not fname:
            E(f"{where}: no Name attribute — SharePoint would generate a permanent internal name")
            continue
        if a("StaticName") != fname:
            E(f"{where}: StaticName must equal Name")
        if not INTERNAL_NAME.match(fname):
            E(f"{where}: internal name must be letters/digits only, start with a letter, max 32 chars")
        if fname in RESERVED:
            E(f"{where}: '{fname}' is reserved or collides with a SharePoint field — prefix it (e.g. {name.split('_', 1)[-1]}{fname})")
        if fname in names:
            E(f"{where}: duplicate internal name")
        names[fname] = el
        fid = a("ID") or ""
        if not GUID.match(fid):
            E(f"{where}: ID must be a fixed {{GUID}} chosen at authoring time")
        else:
            key = fid.lower()
            if key in seen_ids and seen_ids[key] != f"{name}.{fname}":
                E(f"{where}: field ID {fid} is already used by {seen_ids[key]}")
            seen_ids[key] = f"{name}.{fname}"
        if not a("DisplayName"):
            E(f"{where}: no DisplayName")
        ftype = a("Type")
        if ftype in ("Lookup", "LookupMulti"):
            E(f"{where}: Lookup columns do not survive provisioning to another site. Store the target's SharePoint item ID in an indexed Number column named <Target>Id, plus a denormalised display value")
        if ftype in ("Choice", "MultiChoice") and el.find("CHOICES") is None:
            E(f"{where}: Choice field with no <CHOICES>")
        if ftype == "Currency" and not a("LCID"):
            W(f"{where}: Currency field without LCID — SharePoint will use the site locale's currency")

    # A reference to another list is <Target>Id: the target's SharePoint item ID, a whole Number, indexed (it is
    # always filtered on). A Text column named ...Id is allowed only for keys that are not item IDs.
    for fname, el in names.items():
        if fname.endswith("Id") and len(fname) > 2 and el.get("Type") == "Number":
            if el.get("Indexed") != "TRUE":
                E(f"{fname}: a reference column (<Target>Id) must be Indexed=\"TRUE\": it is always filtered on (T-9)")
            if el.get("Decimals") not in ("0", None):
                E(f"{fname}: an item ID has no decimals (Decimals=\"0\")")

    if any(f.get("Type") == "Currency" for f in names.values()) and not any(n.endswith("CurrencyCode") for n in names):
        W("has a Currency field but no ...CurrencyCode field — fine only if PROJECT.md records the project as single-currency")

    # Header and sample rows
    rows = list(csv.reader(io.StringIO(rest)))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        E("line 2 (the header row) is missing")
        return
    header, samples = rows[0], rows[1:]
    known = {f.get("DisplayName") for f in fields} | {f.get("Name") for f in fields}
    unknown = [h for h in header if h and h not in known]
    if unknown:
        W(f"header columns with no matching field (ignored on import): {', '.join(unknown)}")
    if samples and (existing or base_template == 101):
        E("a document library or an existing list takes no sample rows: they can't be imported without a file")
    if len(samples) > MAX_SAMPLE_ROWS:
        E(f"{len(samples)} sample rows — at most {MAX_SAMPLE_ROWS}")
    for i, r in enumerate(samples, start=3):
        cells = " ".join(r)
        for m in EMAIL.finditer(cells):
            if not m.group(0).lower().endswith(SAFE_DOMAINS):
                W(f"line {i}: '{m.group(0)}' looks like a real address — sample rows must be illustrative only")
        for m in URL.finditer(cells):
            if not m.group(1).lower().endswith(SAFE_DOMAINS):
                W(f"line {i}: URL host '{m.group(1)}' looks real — use example.com or {{tenant}}")


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", nargs="?", type=Path, default=ROOT / "schemas")
    ap.add_argument("--prefix", help="list prefix; default: PROJECT.md's 'List prefix'")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")

    prefix = args.prefix or project_prefix()
    files = sorted(p for p in args.folder.glob("*.csv") if not p.name.startswith("_"))
    if not files:
        print(f"No schema CSVs in {args.folder}.")
        return 0
    errors, warnings, seen = [], [], {}
    for f in files:
        check_file(f, prefix, seen, errors, warnings)
    print(f"{len(files)} schema(s) in {args.folder}" + (f", prefix '{prefix}'" if prefix else ", no prefix check (set 'List prefix' in PROJECT.md)"))
    for e in errors:
        print(f"  ERROR    {e}")
    for w in warnings:
        print(f"  WARNING  {w}")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
