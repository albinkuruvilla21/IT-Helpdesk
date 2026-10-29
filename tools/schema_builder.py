"""schema_builder: write SharePoint list schema CSVs (schemas/<PREFIX>_<Entity>.csv) from Python, the way the standard needs them.

Hand-writing escaped XML inside JSON produces broken files; this builds them. Rules it carries (docs/standards/list-schema-standard.md):
  * line 1 is `ListSchema=` + JSON of field XML strings; the FIRST field is SharePoint's base Title, copied verbatim from the sample;
  * every field has an explicit Name = StaticName (internal names are permanent) and a fixed {GUID} that is NEVER regenerated:
    `write()` refuses to touch a CSV that already exists, so re-running a project's script is safe;
  * a reference to another list is a Number column `<Target>Id` (indexed, Min 1) plus a `<Target>Title` text column: use number(..., ref=True);
  * money is `currency()` plus a currency-code text column; yes/no is boolean(); choices are closed at creation;
  * the importer adds at most 5 sample rows and never imports Person or Lookup values; illustrative data only (example.com);
  * indexes: every column a screen or flow filters or sorts by. The base Title column CANNOT be indexed from a schema: index it in list settings;
  * a document library: pass extra={"baseTemplate": 101} and no rows.
After changing a schema AFTER the lists exist on a site: re-run the importer and REFRESH the data source in Studio (PA-T27).

Use (from a project script):
    import sys; sys.path.insert(0, "tools")
    from schema_builder import *
    write("PRJ_Request", [text("ProjectName", "Project Name", "Why this column exists", indexed=True), ...], [["Title", "Project name", ...]])

    uv run tools/schema_builder.py --selftest
"""
import csv
import io
import json
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"
SAMPLE = ROOT / "samples" / "schemas" / "SAMPLE_Announcement.csv"


def _title_field():
    return json.loads(SAMPLE.read_text(encoding="utf-8-sig").split("\n")[0][len("ListSchema="):])["schemaXmlList"][0]


def guid():
    return "{" + str(uuid.uuid4()) + "}"


def attrs(**kw):
    return " ".join(f"{k}={quoteattr(str(v))}" for k, v in kw.items() if v is not None)


def base(name, display, ftype, desc, indexed=False, required=False, **extra):
    a = dict(DisplayName=display, IsModern="TRUE", Name=name, Title=display, Type=ftype)
    if indexed:
        a["Indexed"] = "TRUE"
    if required:
        a["Required"] = "TRUE"
    a.update(extra)
    a.update(ID=guid(), StaticName=name, Description=desc)
    return a


def text(name, display, desc, indexed=False, required=False, maxlen=255):
    return f"<Field {attrs(**base(name, display, 'Text', desc, indexed, required, MaxLength=maxlen))} />", display


def note(name, display, desc, lines=4):
    return f"<Field {attrs(**base(name, display, 'Note', desc, NumLines=lines, RichText='FALSE'))} />", display


def choice(name, display, desc, choices, indexed=False, default=None):
    a = base(name, display, "Choice", desc, indexed, Format="Dropdown", FillInChoice="FALSE")
    inner = "<CHOICES>" + "".join(f"<CHOICE>{escape(c)}</CHOICE>" for c in choices) + "</CHOICES>"
    if default:
        inner += f"<Default>{escape(default)}</Default>"
    return f"<Field {attrs(**a)}>{inner}</Field>", display


def number(name, display, desc, indexed=False, required=False, ref=False, decimals=0):
    extra = dict(Decimals=decimals)
    if ref:
        extra["Min"] = 1
    return f"<Field {attrs(**base(name, display, 'Number', desc, indexed, required, **extra))} />", display


def currency(name, display, desc, lcid=1033):
    return f"<Field {attrs(**base(name, display, 'Currency', desc, Decimals=0, LCID=lcid))} />", display


def date(name, display, desc, indexed=False, only=False):
    fmt = "DateOnly" if only else "DateTime"
    return f"<Field {attrs(**base(name, display, 'DateTime', desc, indexed, Format=fmt, FriendlyDisplayFormat='Disabled'))} />", display


def boolean(name, display, desc, default=0, indexed=False):
    return f"<Field {attrs(**base(name, display, 'Boolean', desc, indexed))}><Default>{default}</Default></Field>", display


def write(listname, fields, rows, extra=None, directory=None):
    """Write schemas/<listname>.csv. Skips (and says so) a file that exists: field GUIDs are never regenerated."""
    path = Path(directory or SCHEMAS) / f"{listname}.csv"
    if path.exists():
        print("exists, left alone:", path.name)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = {"schemaXmlList": [_title_field()] + [x for x, _ in fields]}
    if extra:
        schema.update(extra)
    headers = ["Title"] + [d for _, d in fields]
    buf = io.StringIO()
    w = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\n")
    w.writerow(headers)
    assert len(rows) <= 5, "the importer takes at most 5 sample rows"
    for r in rows:
        assert len(r) == len(headers), (listname, r)
        w.writerow(r)
    path.write_text("ListSchema=" + json.dumps(schema, ensure_ascii=False) + "\n" + buf.getvalue(), encoding="utf-8")
    print("wrote", path.name)


def selftest():
    with tempfile.TemporaryDirectory() as d:
        write("TST_Item", [text("ItemName", "Item Name", "x", indexed=True), choice("ItemKind", "Item Kind", "x", ["A", "B"], default="A"),
                           number("TargetId", "Target Id", "x", indexed=True, ref=True), currency("Price", "Price", "x"), date("DueOn", "Due On", "x", only=True),
                           boolean("IsActive", "Active", "x", default=1), note("Notes", "Notes", "x")],
              [["First", "i1", "A", "1", "10", "2026-10-20", "Yes", "n"]], directory=d)
        first = (Path(d) / "TST_Item.csv").read_text(encoding="utf-8").split("\n")[0]
        xml = json.loads(first[len("ListSchema="):])["schemaXmlList"]
        names = [ET.fromstring(x).get("Name") for x in xml]
        assert names[0] == "Title" and names[1:] == ["ItemName", "ItemKind", "TargetId", "Price", "DueOn", "IsActive", "Notes"], names
        assert all(ET.fromstring(x).get("ID", "{").startswith("{") for x in xml)
        write("TST_Item", [], [], directory=d)  # must be left alone
    print("schema_builder self-test: OK")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(__doc__)
