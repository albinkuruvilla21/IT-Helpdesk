#!/usr/bin/env python3
"""Acies Power Apps template: one command for the whole solution lifecycle.

    uv run tools/pp.py doctor                    check the toolchain
    uv run tools/pp.py setup --client ... --project ... --code CON [--prefix con]
                                                   name the solution, publisher and app; new IDs
    uv run tools/pp.py bump [--part build|minor|major|revision] [--set 1.2.0.0]
    uv run tools/pp.py build [--skip-canvas] [--unmanaged-only]
                                                   canvas source -> .msapp -> solution ZIP(s) -> validate
    uv run tools/pp.py fx [--release]            canvas source checks without packing: YAML, properties, every formula
    uv run tools/pp.py validate [ZIP ...]        offline checks + SolutionPackager round-trip
    uv run tools/pp.py settings [--env ENV]      deployment settings template + completeness check
    uv run tools/pp.py import --env ENV [--activate] [--upgrade] [--yes]
    uv run tools/pp.py export [--env dev] [--zip FILE]
                                                   pull the solution from an environment (or a ZIP) into source
    uv run tools/pp.py check                     Power Apps solution checker (needs pac auth)

Standard library only. Needs the Power Platform CLI (`pac`) on PATH for build, validate's
round-trip, settings, import, export and check. Paths are relative to the template root, so the
folder works on its own when copied out of this repository.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "pp.config.json"

# Component type codes used in Solution.xml RootComponents.
TYPE_WORKFLOW = "29"
TYPE_CANVAS_APP = "300"
# Environment variable definition <type> codes.
EV_TYPES = {
    "100000000": "String", "100000001": "Number", "100000002": "Boolean",
    "100000003": "JSON", "100000004": "Data source", "100000005": "Secret",
}

# Content that must never ship in a solution (PA-T6, PA-T7 in docs/standards/powerapps-traps.md).
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
TENANT_RE = re.compile(r"[A-Za-z0-9-]+\.(?:sharepoint\.com|onmicrosoft\.com)", re.I)
SAS_RE = re.compile(r"[?&]sig=[A-Za-z0-9%+/=]{10,}", re.I)
SECRET_KEY_RE = re.compile(r"(client_?secret|password|api_?key)\"?\s*[:=]\s*\"[^\"]{6,}\"", re.I)


# --------------------------------------------------------------------------- helpers

class Report:
    def __init__(self, title: str) -> None:
        self.title, self.errors, self.warnings, self.passes = title, [], [], []

    def ok(self, msg: str) -> None:
        self.passes.append(msg)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def print(self) -> None:
        print(f"\n== {self.title}")
        for m in self.passes:
            print(f"  PASS  {m}")
        for m in self.warnings:
            print(f"  WARN  {m}")
        for m in self.errors:
            print(f"  FAIL  {m}")
        print(f"  -> {len(self.errors)} error(s), {len(self.warnings)} warning(s)")


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def src_dir(cfg: dict) -> Path:
    return ROOT / cfg["solutionSource"]


def dist_dir(cfg: dict) -> Path:
    return ROOT / cfg["dist"]


BOM = b"\xef\xbb\xbf"


def read_text(p: Path) -> str:
    # newline="" keeps CRLF as written: SolutionPackager writes CRLF and a BOM, and a rewrite
    # that changed either would show every line as changed in git.
    with open(p, encoding="utf-8-sig", newline="") as f:
        return f.read()


def write_text(p: Path, text: str) -> None:
    bom = p.exists() and p.read_bytes()[:3] == BOM
    with open(p, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
        f.write(text)


def pac_path() -> str | None:
    return shutil.which("pac")


def run_pac(args: list[str], quiet: bool = False) -> subprocess.CompletedProcess:
    exe = pac_path()
    if not exe:
        die("the Power Platform CLI (pac) is not on PATH. See README 'Prerequisites'.")
    proc = subprocess.run([exe, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + (proc.stderr or "")
    # pac does not always set a non-zero exit code on failure; look at the text as well.
    failed = proc.returncode != 0 or re.search(r"^\s*(Error:|error )", out, re.M | re.I)
    if failed or not quiet:
        print(out.rstrip())
    if failed:
        die(f"pac {' '.join(args[:2])} failed")
    return proc


def tag(text: str, name: str) -> str | None:
    m = re.search(rf"<{name}>(.*?)</{name}>", text, re.S)
    return m.group(1).strip() if m else None


def solution_identity(cfg: dict) -> dict:
    text = read_text(src_dir(cfg) / "Other" / "Solution.xml")
    pub = text[text.index("<Publisher>"):text.index("</Publisher>")]
    head = text[:text.index("<Publisher>")]
    return {
        "unique": tag(head, "UniqueName"),
        "display": re.search(r'<LocalizedName description="([^"]*)"', head).group(1),
        "version": tag(head, "Version"),
        "publisher": tag(pub, "UniqueName"),
        "publisherDisplay": re.search(r'<LocalizedName description="([^"]*)"', pub).group(1),
        "prefix": tag(pub, "CustomizationPrefix"),
        "optionPrefix": tag(pub, "CustomizationOptionValuePrefix"),
    }


def zip_names(identity: dict) -> tuple[str, str]:
    v = identity["version"].replace(".", "_")
    return f"{identity['unique']}_{v}.zip", f"{identity['unique']}_{v}_managed.zip"


def option_value_prefix(prefix: str) -> int:
    # Deterministic, in Dataverse's allowed range 10000-99999.
    return 10000 + zlib.crc32(prefix.encode()) % 90000


def pascal(text: str) -> str:
    return "".join(w[:1].upper() + w[1:] for w in re.split(r"[^A-Za-z0-9]+", text) if w)


# --------------------------------------------------------------------------- doctor

def cmd_doctor(_: argparse.Namespace) -> None:
    r = Report("Toolchain")
    if sys.version_info >= (3, 10):
        r.ok(f"Python {sys.version.split()[0]}")
    else:
        r.error(f"Python 3.10+ needed, found {sys.version.split()[0]}")
    uv = shutil.which("uv")
    if uv:
        out = subprocess.run([uv, "--version"], capture_output=True, text=True, errors="replace").stdout.strip()
        r.ok(f"{out} (runs the tools with the pinned Python and packages: uv run tools/<tool>.py)")
    else:
        r.warn("uv not found: install it (README, Setting up the Python tools), or pip install --group tools")
    try:
        import yaml  # noqa: F401
        r.ok("PyYAML present: pp.py build parses every .pa.yaml in full (PA1001)")
    except ImportError:
        r.warn("PyYAML missing: only the commonest YAML faults are linted. Run the tools through uv run")
    exe = pac_path()
    if not exe:
        r.error("pac not found. Install: dotnet tool install --global Microsoft.PowerApps.CLI.Tool")
    else:
        out = subprocess.run([exe], capture_output=True, text=True, errors="replace").stdout
        m = re.search(r"Version:\s*([\d.]+)", out)
        r.ok(f"pac {m.group(1) if m else '(version unknown)'} at {exe}")
        auth = subprocess.run([exe, "auth", "list"], capture_output=True, text=True, errors="replace").stdout
        if re.search(r"^\[\d+\]", auth, re.M):
            r.ok("pac auth profile(s) present (needed only for import, export, check)")
        else:
            r.warn("no pac auth profile: build and validate work; import/export/check need `pac auth create`")
    if shutil.which("dotnet"):
        r.ok("dotnet SDK present")
    else:
        r.warn("dotnet not found (needed to install/update pac as a .NET tool)")
    sys.path.insert(0, str(ROOT / "tools"))
    import powerfx
    res, info = powerfx.official_parse([("probe", "If(true, 1, 2)", False)])
    if res is not None and res["probe"]["ok"]:
        r.ok(f"Microsoft's Power Fx parser {info} loads (pwsh): formulas are syntax-checked by it")
    else:
        r.warn(f"Microsoft's Power Fx parser not usable ({info}): formulas fall back to the stdlib parser (powerfx-validation.md §7)")
    r.print()
    sys.exit(1 if r.errors else 0)


# --------------------------------------------------------------------------- setup

def cmd_setup(args: argparse.Namespace) -> None:
    cfg = load_config()
    src = src_dir(cfg)
    old = solution_identity(cfg)

    code = args.code.upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,5}", code):
        die("--code must be 2-6 letters/digits, starting with a letter (e.g. CON)")
    list_prefix = args.list_prefix or code
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{1,9}", list_prefix):
        die("--list-prefix must be letters/digits, starting with a letter")
    prefix = (args.prefix or code).lower()
    if not re.fullmatch(r"[a-z][a-z0-9]{1,7}", prefix) or prefix.startswith("mscrm"):
        die("--prefix must be 2-8 lowercase letters/digits, start with a letter, and not start with 'mscrm'")
    unique = args.solution_name or pascal(f"{args.client} {args.project}")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", unique):
        die("--solution-name must start with a letter and contain only letters, digits and underscores")
    display = args.solution_display or f"{args.client} {args.project}"
    publisher = args.publisher_name or old["publisher"]
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", publisher):
        die("--publisher-name must start with a letter and contain only letters, digits and underscores")
    publisher_display = args.publisher_display or old["publisherDisplay"]
    app_display = args.app_name or args.project

    if old["version"] != "1.0.0.0" and not args.force:
        die(f"the solution is at version {old['version']}, so it has probably been imported somewhere. "
            "Renaming it now would orphan that copy. Re-run with --force if you are sure.")
    if not cfg["canvasApps"] and args.app_name:
        die("--app-name given but pp.config.json lists no canvas app")

    replacements: list[tuple[str, str]] = []  # applied in order to text and to paths

    # New workflow IDs (two solutions sharing a workflow ID overwrite each other's flow).
    for data in sorted((src / "Workflows").glob("*.json.data.xml")):
        old_id = re.search(r'WorkflowId="\{([0-9a-fA-F-]{36})\}"', read_text(data)).group(1).lower()
        new_id = str(uuid.uuid4())
        replacements += [(old_id, new_id), (old_id.upper(), new_id.upper())]

    # New canvas app logical names: <prefix>_<slug>_<5 hex>.
    canvas_moves: list[tuple[Path, Path]] = []
    for app in cfg["canvasApps"]:
        slug = re.sub(r"[^a-z0-9]", "", app_display.lower())[:30] or "app"
        new_name = f"{prefix}_{slug}_{secrets.token_hex(3)[:5]}"
        replacements.append((app["name"], new_name))
        new_source = f"canvas/{pascal(app_display) or 'App'}"
        if new_source != app["source"]:
            canvas_moves.append((ROOT / app["source"], ROOT / new_source))
        app["name"], app["source"] = new_name, new_source
    if args.dev_env:
        cfg["environments"]["dev"]["url"] = args.dev_env

    # The publisher prefix on every schema/logical name.
    if prefix != old["prefix"]:
        replacements.append((f"\x00PREFIX\x00{old['prefix']}_", f"{prefix}_"))

    def apply(text: str) -> str:
        for a, b in replacements:
            if a.startswith("\x00PREFIX\x00"):
                text = re.sub(rf"(?<![A-Za-z0-9]){re.escape(a[8:])}", b, text)
            else:
                text = text.replace(a, b)
        return text

    text_roots = [src, *(ROOT / a["source"] for a in load_config()["canvasApps"]), ROOT / "deployment"]
    binary = re.compile(r"(_BackgroundImageUri|\.msapp|\.msapr|\.png|\.jpg)$", re.I)
    for base in [*text_roots, ROOT / "PROJECT.md"]:
        if not base.exists():
            continue
        for f in base.rglob("*") if base.is_dir() else [base]:
            if f.is_file() and not binary.search(f.name):
                t = read_text(f)
                n = apply(t)
                if n != t:
                    write_text(f, n)
    # Rename files and folders, deepest first.
    for base in text_roots:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*"), key=lambda x: len(x.parts), reverse=True):
            new = apply(p.name)
            if new != p.name:
                p.rename(p.with_name(new))

    # Solution.xml identity.
    sx = src / "Other" / "Solution.xml"
    t = read_text(sx)
    head, rest = t.split("<Publisher>", 1)
    pub, tail = rest.split("</Publisher>", 1)
    head = re.sub(r"<UniqueName>.*?</UniqueName>", f"<UniqueName>{unique}</UniqueName>", head, count=1)
    head = re.sub(r'<LocalizedName description="[^"]*"', f'<LocalizedName description="{xml_attr(display)}"', head, count=1)
    head = re.sub(r"<Version>.*?</Version>", "<Version>1.0.0.0</Version>", head, count=1)
    pub = re.sub(r"<UniqueName>.*?</UniqueName>", f"<UniqueName>{publisher}</UniqueName>", pub, count=1)
    pub = re.sub(r'(<LocalizedName|<Description) description="[^"]*"', rf'\1 description="{xml_attr(publisher_display)}"', pub)
    pub = re.sub(r"<CustomizationPrefix>.*?</CustomizationPrefix>", f"<CustomizationPrefix>{prefix}</CustomizationPrefix>", pub)
    pub = re.sub(r"<CustomizationOptionValuePrefix>.*?</CustomizationOptionValuePrefix>",
                 f"<CustomizationOptionValuePrefix>{option_value_prefix(prefix)}</CustomizationOptionValuePrefix>", pub)
    write_text(sx, head + "<Publisher>" + pub + "</Publisher>" + tail)

    # Canvas apps: move source folders, set display names and new app IDs.
    for frm, to in canvas_moves:
        if to.exists():
            die(f"{to} already exists")
        frm.rename(to)
    for app in cfg["canvasApps"]:
        meta = src / "CanvasApps" / f"{app['name']}.meta.xml"
        mt = read_text(meta)
        write_text(meta, re.sub(r"<DisplayName>.*?</DisplayName>", f"<DisplayName>{xml_text(app_display)}</DisplayName>", mt))
        app_src = ROOT / app["source"]
        yaml = app_src / "Src" / "App.pa.yaml"
        if yaml.exists():
            write_text(yaml, re.sub(r'AppTitle = "[^"]*";', f'AppTitle = "{app_display.replace(chr(34), "")}";', read_text(yaml)))
        for msapr in app_src.glob("*.msapr"):
            target = app_src / f"{pascal(app_display) or 'App'}.msapr"
            rewrite_msapr(msapr, app_display)
            if msapr != target:
                msapr.rename(target)
    save_config(cfg)

    fill_project_card(args, code, list_prefix, unique, display, publisher, prefix, app_display)
    fill_readme(args, code, unique, prefix, app_display)
    print(f"Solution  {unique} ({display}) 1.0.0.0")
    print(f"Publisher {publisher} ({publisher_display}), prefix {prefix}_, option values {option_value_prefix(prefix)}")
    for app in cfg["canvasApps"]:
        print(f"Canvas    {app['name']}  <- {app['source']}")
    print("Next: uv run tools/pp.py build")


def xml_attr(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def xml_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;")


def rewrite_msapr(path: Path, app_display: str) -> None:
    """New app identity inside the .msapr (Properties Id/FileID/Name, PublishInfo AppName)."""
    with zipfile.ZipFile(path) as z:
        entries = {n: z.read(n) for n in z.namelist()}
    for name in list(entries):
        norm = name.replace("\\", "/")
        if norm.endswith("msapp/Properties.json"):
            p = json.loads(entries[name].decode("utf-8-sig"))
            p.update({"Id": str(uuid.uuid4()), "FileID": str(uuid.uuid4()), "Name": app_display})
            entries[name] = json.dumps(p, indent=2).encode()
        elif norm.endswith("msapp/Resources/PublishInfo.json"):
            p = json.loads(entries[name].decode("utf-8-sig"))
            p["AppName"] = app_display
            entries[name] = json.dumps(p, indent=2).encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in entries.items():
            z.writestr(n, data)


def fill_readme(args, code, unique, prefix, app_display) -> None:
    """README.md's introduction and getting-started blocks become the project's own (docs/templates/project-readme.template.md).
    The how-to sections between and after them stay. Blocks are marked <!-- README:intro --> and <!-- README:start -->."""
    readme, tpl = ROOT / "README.md", ROOT / "docs" / "templates" / "project-readme.template.md"
    if not readme.exists() or not tpl.exists():
        return
    values = {"{Client}": args.client, "{Project}": args.project, "{CODE}": code, "{solution}": unique,
              "{prefix}": prefix, "{app}": app_display}
    source = read_text(tpl)
    for k, v in values.items():
        source = source.replace(k, v)
    text = read_text(readme)
    nl = "\r\n" if "\r\n" in text else "\n"
    source = source.replace("\r\n", "\n").replace("\n", nl)
    for block in ("intro", "start"):
        pat = re.compile(rf"<!-- README:{block} -->.*?<!-- /README:{block} -->", re.S)
        new = pat.search(source)
        if not new or not pat.search(text):
            print(f"README.md: no <!-- README:{block} --> block to replace; left as it is")
            continue
        text = pat.sub(lambda _: new.group(0), text, count=1)
    write_text(readme, text)


def fill_project_card(args, code, list_prefix, unique, display, publisher, prefix, app_display) -> None:
    card = ROOT / "PROJECT.md"
    if not card.exists():
        return
    t = read_text(card)
    rows = {
        "Client": args.client, "Project": args.project, "Project code": code, "List prefix": list_prefix,
        "Solution unique name": unique, "Solution display name": display, "Publisher": publisher,
        "Publisher prefix": f"`{prefix}_`", "Canvas app": app_display,
    }
    if args.dev_env:
        rows["Dev environment"] = args.dev_env
    if args.dev_site:
        rows["Dev site"] = args.dev_site
    for label, value in rows.items():
        t = re.sub(rf"^\| {re.escape(label)} \|[^\r\n]*", lambda _: f"| {label} | {value} |", t, count=1, flags=re.M)
    write_text(card, t)


# --------------------------------------------------------------------------- bump

def cmd_bump(args: argparse.Namespace) -> None:
    cfg = load_config()
    sx = src_dir(cfg) / "Other" / "Solution.xml"
    t = read_text(sx)
    cur = tag(t, "Version")
    parts = [int(x) for x in cur.split(".")] + [0] * (4 - len(cur.split(".")))
    if args.set:
        if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", args.set):
            die("--set needs a four-part version, e.g. 1.2.0.0")
        new = args.set
        if [int(x) for x in new.split(".")] <= parts:
            die(f"{new} is not higher than {cur}. Dataverse only upgrades to a higher version.")
    else:
        i = {"major": 0, "minor": 1, "build": 2, "revision": 3}[args.part]
        parts[i] += 1
        parts[i + 1:] = [0] * (3 - i)
        new = ".".join(map(str, parts))
    write_text(sx, t.replace(f"<Version>{cur}</Version>", f"<Version>{new}</Version>", 1))
    print(f"{cur} -> {new}")


# --------------------------------------------------------------------------- build

def cmd_build(args: argparse.Namespace) -> None:
    cfg = load_config()
    identity = solution_identity(cfg)
    dist = dist_dir(cfg)
    stage = dist / "stage"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(src_dir(cfg), stage)
    # SolutionPackager packs a managed ZIP only from a manifest marked Managed=2 ("both"); an export
    # writes 0. Mark the staging copy, never the source: the output ZIP gets 0 or 1 as requested.
    sx = stage / "Other" / "Solution.xml"
    write_text(sx, re.sub(r"<Managed>\d</Managed>", "<Managed>2</Managed>", read_text(sx), count=1))

    canvas_dir = stage / "CanvasApps"
    if args.skip_canvas:
        if canvas_dir.exists():
            shutil.rmtree(canvas_dir)
        sx = stage / "Other" / "Solution.xml"
        write_text(sx, re.sub(rf'\s*<RootComponent type="{TYPE_CANVAS_APP}"[^>]*/>', "", read_text(sx)))
        print("Canvas apps left out (--skip-canvas).")
    else:
        for app in cfg["canvasApps"]:
            source = ROOT / app["source"]
            if not (source / "Src").is_dir():
                die(f"canvas source {source}/Src not found (pp.config.json canvasApps)")
            target = canvas_dir / f"{app['name']}_DocumentUri.msapp"
            if target.exists():
                target.unlink()
            print(f"Packing canvas app {app['name']} from {app['source']}")
            run_pac(["canvas", "pack", "--sources", str(source), "--msapp", str(target), "--layout", "SourceCode"], quiet=True)
            # The same .msapp on its own, to open directly in Studio (Open → Browse) without an import.
            dist.mkdir(exist_ok=True)
            shutil.copyfile(target, dist / f"{Path(app['source']).name}.msapp")
            # Studio stamps AppVersion on every save; a re-import with an unchanged stamp may be taken as
            # the same document (PA-T19). Stamp the build time, in the staged copy only.
            meta = canvas_dir / f"{app['name']}.meta.xml"
            if meta.exists():
                stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                write_text(meta, re.sub(r"<AppVersion>[^<]*</AppVersion>", f"<AppVersion>{stamp}</AppVersion>", read_text(meta), count=1))
        for meta in canvas_dir.glob("*.meta.xml") if canvas_dir.exists() else []:
            name = meta.name[: -len(".meta.xml")]
            if not (canvas_dir / f"{name}_DocumentUri.msapp").exists():
                die(f"{meta.name} has no .msapp: add it to pp.config.json canvasApps with its source folder")

    dist.mkdir(exist_ok=True)
    unmanaged, managed = zip_names(identity)
    outputs = [(dist / unmanaged, "Unmanaged")]
    if cfg.get("buildManaged", True) and not args.unmanaged_only:
        outputs.append((dist / managed, "Managed"))
    for path, kind in outputs:
        if path.exists():
            path.unlink()
        print(f"Packing {kind.lower()} solution -> {path.relative_to(ROOT)}")
        run_pac(["solution", "pack", "--zipfile", str(path), "--folder", str(stage), "--packagetype", kind], quiet=True)
    shutil.rmtree(stage)

    reports = [validate_zip(path, cfg, kind == "Managed") for path, kind in outputs]
    for r in reports:
        r.print()
    if any(r.errors for r in reports):
        die("build produced a package that failed validation")
    print(f"\nBuilt {identity['unique']} {identity['version']}:")
    for path, _ in outputs:
        print(f"  {path.relative_to(ROOT)}  ({path.stat().st_size:,} bytes)")


# --------------------------------------------------------------------------- validate

def scan_content(r: Report, where: str, text: str) -> None:
    for m in set(EMAIL_RE.findall(text)):
        if not m.lower().endswith(("@example.com", "@contoso.com")):
            r.error(f"{where}: hard-coded email address '{m}' (use an environment variable)")
    for m in set(TENANT_RE.findall(text)):
        r.error(f"{where}: hard-coded tenant URL '{m}' (use an environment variable)")
    if SAS_RE.search(text):
        r.error(f"{where}: signed storage URL (SAS token)")
    if SECRET_KEY_RE.search(text):
        r.error(f"{where}: looks like a secret")


def validate_zip(path: Path, cfg: dict, managed: bool, roundtrip: bool = True) -> Report:
    r = Report(f"Validate {path.name}")
    try:
        # Read everything and close at once: on Windows an open handle stops pac reading the file.
        with zipfile.ZipFile(path) as z:
            contents = {n.replace("\\", "/").lstrip("/"): z.read(n) for n in z.namelist()}
    except (zipfile.BadZipFile, FileNotFoundError) as e:
        r.error(f"not a readable ZIP: {e}")
        return r
    names = contents

    def read(n: str) -> bytes:
        return contents[n.lstrip("/")]

    for required in ("[Content_Types].xml", "solution.xml", "customizations.xml"):
        if required in names:
            continue
        r.error(f"missing {required} at the ZIP root (zip the folder's contents, not the folder)")
    if r.errors:
        return r
    r.ok("[Content_Types].xml, solution.xml and customizations.xml at the root")

    # solution.xml
    try:
        sol = ET.fromstring(read("solution.xml"))
    except ET.ParseError as e:
        r.error(f"solution.xml does not parse: {e}")
        return r
    man = sol.find("SolutionManifest")
    unique = man.findtext("UniqueName", "")
    version = man.findtext("Version", "")
    is_managed = man.findtext("Managed", "")
    pub = man.find("Publisher")
    prefix = pub.findtext("CustomizationPrefix", "")
    opt = pub.findtext("CustomizationOptionValuePrefix", "")
    pub_name = pub.findtext("UniqueName", "")
    (r.ok if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", unique) else r.error)(f"unique name '{unique}'")
    (r.ok if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", version) else r.error)(f"version '{version}' (four parts)")
    if is_managed != ("1" if managed else "0"):
        r.error(f"Managed={is_managed}, expected {'1' if managed else '0'}")
    else:
        r.ok(f"package type {'managed' if managed else 'unmanaged'}")
    if pub_name.lower().startswith("defaultpublisher") or prefix in ("new", "cr"):
        r.error(f"publisher '{pub_name}' / prefix '{prefix}' is a default publisher: use the project publisher (PA-T1)")
    elif not re.fullmatch(r"[a-z][a-z0-9]{1,7}", prefix):
        r.error(f"publisher prefix '{prefix}' must be 2-8 lowercase letters/digits")
    else:
        r.ok(f"publisher {pub_name}, prefix {prefix}_")
    if not (opt.isdigit() and 10000 <= int(opt) <= 99999):
        r.error(f"option value prefix '{opt}' must be 10000-99999")
    roots = man.find("RootComponents")
    root_flows = {c.get("id", "").strip("{}").lower() for c in roots if c.get("type") == TYPE_WORKFLOW}
    root_apps = {c.get("schemaName") for c in roots if c.get("type") == TYPE_CANVAS_APP}
    missing = man.find("MissingDependencies")
    if missing is not None and len(missing):
        r.warn(f"{len(missing)} missing dependency entries: the target environment must already have them")

    # customizations.xml
    try:
        cust = ET.fromstring(read("customizations.xml"))
    except ET.ParseError as e:
        r.error(f"customizations.xml does not parse: {e}")
        return r
    allowed = set(cfg.get("allowedConnectors", []))
    conn_refs = {}
    for cr in cust.iterfind("connectionreferences/connectionreference"):
        name = cr.get("connectionreferencelogicalname", "")
        connector = cr.findtext("connectorid", "").rsplit("/", 1)[-1]
        conn_refs[name] = connector
        if not name.startswith(f"{prefix}_"):
            r.error(f"connection reference '{name}' does not use the publisher prefix")
        if connector not in allowed:
            r.error(f"connection reference '{name}' uses '{connector}', not in allowedConnectors (D2: standard connectors only)")
    by_connector: dict[str, list[str]] = {}
    for n, c in conn_refs.items():
        by_connector.setdefault(c, []).append(n)
    for c, ns in by_connector.items():
        if len(ns) > 1:
            r.warn(f"{len(ns)} connection references for {c} ({', '.join(sorted(ns))}): one per connector is enough (PA-T3)")
    r.ok(f"{len(conn_refs)} connection reference(s)")

    # Environment variables
    env_defs = {}
    for n in names:
        m = re.fullmatch(r"environmentvariabledefinitions/([^/]+)/environmentvariabledefinition\.xml", n)
        if m:
            d = ET.fromstring(read(n))
            env_defs[d.get("schemaname")] = d
        if re.fullmatch(r"environmentvariabledefinitions/[^/]+/environmentvariablevalues\.json", n):
            r.error(f"{n}: a current value is packaged. Values belong in deployment/settings.<env>.json (PA-T4)")
    for schema, d in env_defs.items():
        t = d.findtext("type", "")
        if not schema.startswith(f"{prefix}_"):
            r.error(f"environment variable '{schema}' does not use the publisher prefix")
        if t not in EV_TYPES:
            r.error(f"environment variable '{schema}' has unknown type {t}")
        if t == "100000005":
            r.error(f"environment variable '{schema}' is a Secret (Azure Key Vault): D3/D7 need an override in PROJECT.md")
        parent = d.findtext("parentdefinitionid/schemaname")
        if parent and parent not in env_defs:
            r.error(f"environment variable '{schema}' has parent '{parent}', which is not in the solution")
        if parent:  # a list variable: Studio names the data source after the variable's DISPLAY name, so formulas would not find the list (PA-T32)
            shown = d.find("displayname").get("default", "") if d.find("displayname") is not None else ""
            lists = {f.stem for f in (ROOT / "schemas").glob("*.csv")} if (ROOT / "schemas").is_dir() else set()
            if lists and shown not in lists:
                r.error(f"environment variable '{schema}' is a list but its display name is '{shown}': Studio names the data source by it, so formulas that name the list "
                        f"cannot find it. Set the display name to the list name, one of {', '.join(sorted(lists))} (PA-T32)")
        if re.search(r"(^|_)test_|_test$", schema, re.I):
            r.warn(f"environment variable '{schema}' looks like a per-environment copy: one variable, one value per environment (PA-T2)")
        scan_content(r, f"env var {schema}", ET.tostring(d, encoding="unicode"))
    r.ok(f"{len(env_defs)} environment variable definition(s)")

    # Flows
    flows = cust.findall("Workflows/Workflow")
    for wf in flows:
        wid = wf.get("WorkflowId", "").strip("{}").lower()
        label = wf.get("Name", wid)
        if wid not in root_flows:
            r.warn(f"flow '{label}' is not a root component")
        jf = wf.findtext("JsonFileName", "")
        if jf.lstrip("/") not in names:
            r.error(f"flow '{label}': {jf} is not in the ZIP")
            continue
        raw = read(jf).decode("utf-8-sig")
        try:
            flow = json.loads(raw)
        except json.JSONDecodeError as e:
            r.error(f"flow '{label}': JSON does not parse: {e}")
            continue
        validate_flow(r, label, flow, conn_refs, env_defs, cfg)
    r.ok(f"{len(flows)} cloud flow(s)")
    missing_flows = root_flows - {wf.get("WorkflowId", "").strip("{}").lower() for wf in flows}
    for m in missing_flows:
        r.error(f"root component workflow {m} has no Workflow entry in customizations.xml")

    # Canvas apps
    apps = cust.findall("CanvasApps/CanvasApp")
    for app in apps:
        name = app.findtext("Name", "")
        if name not in root_apps:
            r.warn(f"canvas app '{name}' is not a root component")
        if not name.startswith(f"{prefix}_"):
            r.error(f"canvas app '{name}' does not use the publisher prefix")
        for el in ("DocumentUri", "BackgroundImageUri"):
            uri = app.findtext(el, "")
            if uri.lstrip("/") not in names:
                r.error(f"canvas app '{name}': {el} {uri} is not in the ZIP")
        doc = app.findtext("DocumentUri", "").lstrip("/")
        if doc in names:
            validate_msapp(r, name, read(doc))
        try:
            refs = json.loads(app.findtext("ConnectionReferences") or "{}")
        except json.JSONDecodeError:
            refs = {}
        for ref in refs.values():
            api = str(ref.get("id", "")).rsplit("/", 1)[-1]
            if api and api not in allowed:
                r.error(f"canvas app '{name}' uses connector '{api}', not in allowedConnectors (D2)")
    for a in root_apps - {app.findtext("Name") for app in apps}:
        r.error(f"root component canvas app {a} has no CanvasApp entry in customizations.xml")
    r.ok(f"{len(apps)} canvas app(s)")

    if roundtrip and pac_path():
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [pac_path(), "solution", "unpack", "--zipfile", str(path), "--folder", tmp,
                 "--packagetype", "Managed" if managed else "Unmanaged"],
                capture_output=True, text=True, errors="replace")
            out = proc.stdout + proc.stderr
            if proc.returncode == 0 and "complete" in out.lower():
                r.ok("SolutionPackager unpacks it (pac solution unpack)")
            else:
                r.error("SolutionPackager could not unpack it:\n" + out[-1500:])
    elif roundtrip:
        r.warn("pac not found: SolutionPackager round-trip skipped")
    return r


def validate_flow(r: Report, label: str, flow: dict, conn_refs: dict, env_defs: dict, cfg: dict) -> None:
    props = flow.get("properties", {})
    definition = props.get("definition", {})
    allowed = set(cfg.get("allowedConnectors", []))
    for key, ref in props.get("connectionReferences", {}).items():
        api = ref.get("api", {}).get("name", "")
        logical = ref.get("connection", {}).get("connectionReferenceLogicalName")
        if not logical:
            r.error(f"flow '{label}': connection '{key}' is not a connection reference (embedded connection)")
        elif logical not in conn_refs:
            r.error(f"flow '{label}': connection reference '{logical}' is not in the solution")
        if api and api not in allowed:
            r.error(f"flow '{label}': connector '{api}' not in allowedConnectors (D2)")
    params = definition.get("parameters", {})
    for pname, p in params.items():
        schema = (p.get("metadata") or {}).get("schemaName")
        if not schema:
            continue
        if schema not in env_defs:
            r.error(f"flow '{label}': parameter '{pname}' points to environment variable '{schema}', not in the solution")
        if p.get("defaultValue") not in ("", None, {}, []):
            r.error(f"flow '{label}': parameter '{pname}' carries a value ({str(p['defaultValue'])[:60]}). "
                    "Clear it; the environment variable supplies it (PA-T5)")
    used = set(re.findall(r"parameters\('([^']+)'\)", json.dumps(definition)))
    for u in used - set(params) - {"$authentication", "$connections"}:
        r.error(f"flow '{label}': uses parameters('{u}') which is not declared")
    kinds = set(cfg.get("allowedRequestTriggerKinds", []))

    def walk(node: dict, where: str) -> None:
        for name, step in node.items():
            t = step.get("type", "")
            if t in ("Http", "HttpWebhook"):
                r.error(f"flow '{label}': {where} '{name}' is an HTTP {where} (premium, D2)")
            if t == "Request" and step.get("kind") not in kinds:
                r.error(f"flow '{label}': trigger '{name}' kind '{step.get('kind')}' (HTTP request triggers are premium, D2)")
            for sub in ("actions",):
                if isinstance(step.get(sub), dict):
                    walk(step[sub], "action")
            if isinstance(step.get("else"), dict) and isinstance(step["else"].get("actions"), dict):
                walk(step["else"]["actions"], "action")
            for case in (step.get("cases") or {}).values():
                walk(case.get("actions", {}), "action")
            if isinstance(step.get("default"), dict):
                walk(step["default"].get("actions", {}), "action")

    walk(definition.get("triggers", {}), "trigger")
    walk(definition.get("actions", {}), "action")
    # Values the env vars should hold, hard-coded instead.
    text = json.dumps(definition)
    scan_content(r, f"flow '{label}'", text)
    if re.search(r'"source":\s*"sites/[^"]+,[0-9a-f-]{36},', text):
        r.error(f"flow '{label}': hard-coded SharePoint site ID (sites/<host>,<guid>,<guid>) (PA-T5)")


def validate_msapp(r: Report, name: str, data: bytes) -> None:
    import io
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        r.error(f"canvas app '{name}': .msapp is not a valid archive")
        return
    entries = {n.replace("\\", "/"): n for n in z.namelist()}
    for need in ("Header.json", "Properties.json"):
        if need not in entries:
            r.error(f"canvas app '{name}': .msapp has no {need}")
    yaml = {n: z.read(entries[n]).decode("utf-8-sig", "replace")
            for n in entries if n.startswith("Src/") and n.endswith(".pa.yaml")}
    for n, text in yaml.items():
        scan_content(r, f"canvas app '{name}' {n}", text)
    if yaml and "References/Templates.json" in entries:
        templates = json.loads(z.read(entries["References/Templates.json"]).decode("utf-8-sig"))
        datasources = data_source_names(z.read(entries["References/DataSources.json"])) if "References/DataSources.json" in entries else []
        check_control_properties(r, name, templates, yaml)
        check_source_rules(r, name, yaml)
        check_formulas(r, name, yaml, templates, datasources)
    if not any(n.startswith("Controls/") for n in entries):
        r.warn(f"canvas app '{name}': no App control (Controls/1.json). Studio may refuse to open it with "
               "ErrOpeningDocument_UnknownError (PA-T20)")
    packed = json.loads(z.read(entries["packed.json"]).decode("utf-8-sig")) if "packed.json" in entries else {}
    if packed.get("LoadConfiguration", {}).get("LoadFromYaml"):
        r.warn(f"canvas app '{name}' was packed from YAML: open it once in Power Apps Studio, then Save and "
               "Publish, before users run it (PA-T8)")


# Screen and App properties are not in Templates.json; unknown ones only warn.
SCREEN_PROPS = {"Fill", "BackgroundImage", "ImagePosition", "OnVisible", "OnHidden", "LoadingSpinner",
                "LoadingSpinnerColor", "Height", "Width", "Orientation", "Size"}
APP_PROPS = {"Formulas", "OnStart", "StartScreen", "Theme", "OnError", "BackEnabled", "ConfirmExit",
             "ConfirmExitMessage", "SizeBreakpoints", "MinScreenWidth", "MinScreenHeight"}
# An auto-layout container gives these to its children; they are not in the child's own template.
CONTAINER_CHILD_PROPS = {"FillPortions", "AlignInContainer", "LayoutMinWidth", "LayoutMinHeight",
                         "LayoutMaxWidth", "LayoutMaxHeight"}


def yaml_property_blocks(text: str):
    """Yield (control_type or None, owner, property names) for each Properties: block in a .pa.yaml.

    The Source Code layout is regular enough to read without a YAML library: a control is
    `- name:` / `Control: Type@ver` / `Properties:` with one property per line at a deeper indent.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)Properties:\s*$", line)
        if not m:
            continue
        indent = len(m.group(1))
        # The block's owner: the nearest preceding line at the same indent (`Control: ...`) or less.
        ctype, owner = None, ""
        for back in range(i - 1, -1, -1):
            b = lines[back]
            if not b.strip() or b.lstrip().startswith("#"):
                continue
            bi = len(b) - len(b.lstrip())
            if bi == indent and (c := re.match(r"\s*Control:\s*(\S+)", b)):
                ctype = c.group(1)
            elif bi < indent:
                owner = b.strip().lstrip("- ").rstrip(":")
                break
        props, child_indent = [], None
        for nxt in lines[i + 1:]:
            if not nxt.strip() or nxt.lstrip().startswith("#"):
                continue
            ni = len(nxt) - len(nxt.lstrip())
            if ni <= indent:
                break
            child_indent = child_indent or ni
            if ni == child_indent and (k := re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", nxt)):
                props.append(k.group(1))
        yield ctype, owner, props


def _lint_yaml_syntax(r: Report, app: str, path: str, text: str) -> None:
    """PA1001 (`YamlInvalidSyntax`): Studio refuses a file that is not valid YAML, and `pac canvas pack` does not say so.

    Always checks the commonest cause: text after the closing quote of a single-quoted value (for example a comment
    appended to a quoted formula). The whole file is then parsed with PyYAML (in pyproject.toml; a warning when it is missing)."""
    lines = text.splitlines()
    in_block = None
    for n, line in enumerate(lines, 1):
        ind = len(line) - len(line.lstrip())
        if in_block is not None:
            if line.strip() and ind <= in_block:
                in_block = None
            else:
                continue
        m = re.match(r"^(\s*)(?:- )?[A-Za-z_][A-Za-z0-9_]*: (.*)$", line)
        if not m:
            continue
        val = m.group(2)
        if re.match(r"^[|>][+-]?$", val.strip()):
            in_block = ind
            continue
        if val.startswith("'"):
            i = 1
            while i < len(val):
                if val[i] == "'":
                    if i + 1 < len(val) and val[i + 1] == "'":
                        i += 2
                        continue
                    break
                i += 1
            else:
                r.error(f"canvas app '{app}' {path} line {n}: a single-quoted value is not closed (PA1001)")
                continue
            rest = val[i + 1:].strip()
            if rest and not rest.startswith("#"):
                r.error(f"canvas app '{app}' {path} line {n}: text after the closing quote of a quoted value: ...{rest[:40]} (PA1001). A comment must go inside the quotes")
    try:
        import yaml as _yaml
    except ImportError:
        r.warn(f"canvas app '{app}' {path}: PyYAML is not installed, so only the commonest YAML faults were checked (PA1001). Run the tools through uv run")
        return
    try:
        _yaml.safe_load(text)
    except _yaml.YAMLError as e:
        r.error(f"canvas app '{app}' {path}: not valid YAML ({str(e).splitlines()[0]}) (PA1001)")


def data_source_names(raw: bytes) -> list[str]:
    """Names of the data sources Studio has added to the app (References/DataSources.json): lists, connectors, flows."""
    try:
        return [d.get("Name", "") for d in json.loads(raw.decode("utf-8-sig")).get("DataSources", []) if d.get("Name")]
    except (ValueError, AttributeError):
        return []


def app_references(source: Path) -> tuple[dict, list[str]]:
    """The control templates and data sources recorded in a canvas source folder's .msapr or .msapp (empty when there is none)."""
    for msapr in [*source.glob("*.msapr"), *source.glob("*.msapp")]:
        with zipfile.ZipFile(msapr) as z:
            names = {n.replace("\\", "/"): n for n in z.namelist()}
            tpl = next((names[n] for n in names if n.endswith("References/Templates.json")), None)
            ds = next((names[n] for n in names if n.endswith("References/DataSources.json")), None)
            return (json.loads(z.read(tpl).decode("utf-8-sig")) if tpl else {}), (data_source_names(z.read(ds)) if ds else [])
    return {}, []


def formula_check_args(templates: dict, datasources: list[str]) -> dict:
    """What tools/powerfx.py needs from the app: each control type's property list, and the data sources Studio knows."""
    known, _ = control_template_index(templates)

    def props_for(ctype: str):
        return known.get(template_key(ctype))
    return {"props_for": props_for, "screen_props": SCREEN_PROPS, "child_props": CONTAINER_CHILD_PROPS, "datasources": datasources}


def check_formulas(r: Report, app: str, yaml: dict[str, str], templates: dict, datasources: list[str], release: bool = False,
                   official: bool = True) -> None:
    """Every Power Fx formula, statically (docs/standards/powerfx-validation.md; the checks are in tools/powerfx.py).

    Syntax by Microsoft's own parser (pac's Microsoft.PowerFx.Core, through PowerShell 7) when it is available; then function names and
    argument counts, behaviour functions outside On... properties, names, control properties, enumerations, literal types, list columns
    (schemas/*.csv), Patch, delegation and indexes, variables, flow calls and acceptance-criteria comments. A formula Studio refuses
    does NOTHING when it runs (no message), so these are errors where the rule is certain. None of this replaces opening the app in
    Studio: Studio binds every name and type, and only the running app proves the behaviour.

    A flow the app calls compiles only once it is ADDED TO THE APP in Studio, from the app opened inside the imported solution (PA-T26):
    reported as one warning so it is never a surprise."""
    sys.path.insert(0, str(ROOT / "tools"))
    import powerfx
    res = powerfx.check_app(app, yaml, release=release, use_official=official, **formula_check_args(templates, datasources))
    for f in res.errors:
        r.error(f"canvas app '{app}' {f.text()}")
    for f in res.warnings:
        r.warn(f"canvas app '{app}' {f.text()}")
    for f, reason in res.suppressed:
        r.warn(f"canvas app '{app}' {f.where()}: {f.code} suppressed by fx-ignore ({reason}): {f.message}")
    if res.flows_used:
        r.warn(f"canvas app '{app}': {len(res.flows_used)} flow(s) are called from formulas ({', '.join(res.flows_used)}). Studio marks every button that calls one as an error, and it does nothing, until the flows are added to the app: import the solution, open the app FROM the solution, then Data > Add data > Flows (PA-T26)")
    s = res.stats
    parser = (f"syntax confirmed by Microsoft's Power Fx parser {res.official_version}" if res.official_version else
              f"syntax checked by the stdlib parser only ({res.official_reason})")
    if not res.official_version:
        r.warn(f"canvas app '{app}': Microsoft's Power Fx parser was not used: {res.official_reason}. Install pac and PowerShell 7 for the authoritative syntax check")
    r.ok(f"canvas app '{app}': {s['formulas']} formula(s), {parser}; {s['calls']} function call(s) and {s['names']} name(s) checked, "
         f"{s['unverified_scope']} name(s) in record scope of an unknown table not checked, {s['delegation_sites']} list query(ies) and "
         f"{s['writes']} write(s) checked. Static only: open the app in Studio to bind and type-check")


def check_source_rules(r: Report, app: str, yaml: dict[str, str]) -> None:
    """Rules Studio enforces on open that neither `pac canvas pack` nor the property check catch.

    PA2110: two controls on one screen share a name. PA-T21: `LayoutMode` on an auto-layout or manual-layout
    container and `Layout` on a gallery are rejected by Studio (PA2108), although the control's template lists them.
    """
    for path, text in sorted(yaml.items()):
        if path.endswith(".pa.yaml"):
            _lint_yaml_syntax(r, app, path, text)
        if not path.endswith(".pa.yaml") or path.endswith("_EditorState.pa.yaml") or path.endswith("App.pa.yaml"):
            continue
        lines = text.splitlines()
        seen: dict[str, int] = {}
        for i, line in enumerate(lines):
            m = re.match(r"^(\s*)- ([A-Za-z_][A-Za-z0-9_]*):\s*$", line)
            if not m or i + 1 >= len(lines) or "Control:" not in lines[i + 1]:
                continue
            ind, cname = len(m.group(1)), m.group(2)
            if cname in seen:
                r.error(f"canvas app '{app}' {path}: control name '{cname}' is used twice (line {seen[cname]} and {i + 1}). Studio refuses it (PA2110)")
            seen[cname] = i + 1
            ctype = re.search(r"Control:\s*(\S+)", lines[i + 1]).group(1)
            variant = ""
            j = i + 2
            while j < len(lines) and len(lines[j]) - len(lines[j].lstrip()) == ind + 4 and not lines[j].strip().startswith("Properties:"):
                if lines[j].strip().startswith("Variant:"):
                    variant = lines[j].split(":", 1)[1].strip()
                j += 1
            bad = None
            if ctype.startswith("GroupContainer") and variant in ("AutoLayout", "ManualLayout"):
                bad = "LayoutMode"
            elif ctype.startswith("Gallery") and variant:
                bad = "Layout"
            if bad:
                k = j + 1
                while k < len(lines) and len(lines[k]) - len(lines[k].lstrip()) > ind + 4:
                    if re.match(rf"\s*{bad}\s*:", lines[k]) and len(lines[k]) - len(lines[k].lstrip()) == ind + 6:
                        r.error(f"canvas app '{app}' {path}: '{cname}' ({ctype}, variant {variant}) sets {bad}. Studio refuses it (PA2108, PA-T21)")
                    k += 1


def control_template_index(templates: dict) -> tuple[dict[tuple[str, str], set[str]], set[str]]:
    """{(template name, version): property names} and the code-component versions, from Studio's templates."""
    known: dict[tuple[str, str], set[str]] = {}
    # Fallback first, so the app's own templates win: tools/canvas-control-templates.json holds the
    # property lists of the controls a Studio-saved app may not have packed yet (e.g. a gallery
    # Claude added to YAML before anyone opened the app).
    reference = ROOT / "tools" / "canvas-control-templates.json"
    pcf_versions: set[str] = set()
    if reference.exists():
        ref = json.loads(read_text(reference))
        for t in ref.get("UsedTemplates", []):
            known[(t["Name"], t["Version"])] = set(t["Properties"])
        pcf_versions |= {p["Version"] for p in ref.get("PcfTemplates", [])}
    for t in templates.get("UsedTemplates", []):
        xml = t.get("Template", "")
        props = re.findall(r'<(?:appMagic:)?(?:includeProperty|property) name="([^"]+)"', xml)
        known[(t["Name"], t.get("Version", ""))] = set(props)
    pcf_versions |= {p.get("Version") for p in templates.get("PcfTemplates", [])}
    return known, pcf_versions


def template_key(ctype: str) -> tuple[str, str]:
    """`Classic/TextInput@2.3.2` -> ('text', '2.3.2'); `Label@2.5.1` -> ('label', '2.5.1')."""
    base, _, version = ctype.partition("@")
    classic = base.startswith("Classic/")
    base = base.split("/")[-1]
    return ("text" if (classic and base == "TextInput") else base[:1].lower() + base[1:]), version


def check_control_properties(r: Report, app: str, templates: dict, yaml: dict[str, str]) -> None:
    """Every control property must exist in Studio's own control template (References/Templates.json).

    pac canvas pack does not check this; Studio does, on open (PA2108). Catch it at build time.
    """
    known, pcf_versions = control_template_index(templates)
    unverified: set[str] = set()
    checked = 0
    for path, text in sorted(yaml.items()):
        for ctype, owner, props in yaml_property_blocks(text):
            if ctype is None:
                allowed = APP_PROPS if owner == "App" else SCREEN_PROPS
                for p in props:
                    if p not in allowed:
                        r.warn(f"canvas app '{app}' {path}: '{owner}' property '{p}' is not one this check knows")
                continue
            tname, version = template_key(ctype)
            classic = ctype.startswith("Classic/")
            props_ok = known.get((tname, version))
            if props_ok is None:
                versions = sorted(v for (n, v) in known if n == tname)
                if not classic and version in pcf_versions:
                    unverified.add(ctype)  # a modern (code component) control, e.g. Text@0.0.51
                elif versions:
                    r.error(f"canvas app '{app}' {path}: '{owner}' is {ctype}, but this app's templates have "
                            f"{tname} {', '.join(versions)} (PA2106)")
                else:
                    unverified.add(ctype)  # no template packed (form data cards, or a control Studio adds on load)
                continue
            checked += 1
            for p in props:
                if p not in props_ok and p not in CONTAINER_CHILD_PROPS:
                    r.error(f"canvas app '{app}' {path}: unknown property '{p}' on '{owner}' ({ctype}). "
                            "Studio will refuse it (PA2108, PA-T17)")
    if unverified:
        r.warn(f"canvas app '{app}': properties of {', '.join(sorted(unverified))} not checked "
               "(no property list packed for them). Open the app in Studio to confirm (PA-T17)")
    r.ok(f"canvas app '{app}': {checked} control(s) checked against Studio's control templates")


def cmd_fx(args: argparse.Namespace) -> None:
    """The canvas checks on source, without packing: YAML, control properties, and every formula (fast; run after each edit)."""
    cfg = load_config()
    reports = []
    for app in cfg["canvasApps"]:
        source = ROOT / app["source"]
        if not (source / "Src").is_dir():
            die(f"canvas source {source}/Src not found (pp.config.json canvasApps)")
        yaml = {f"Src/{p.name}": read_text(p) for p in sorted((source / "Src").glob("*.pa.yaml"))}
        templates, datasources = app_references(source)
        r = Report(f"Formulas: {app['name']} ({app['source']}){' — release' if args.release else ''}")
        for n, text in yaml.items():
            scan_content(r, f"canvas app '{app['name']}' {n}", text)
        check_control_properties(r, app["name"], templates, yaml)
        check_source_rules(r, app["name"], yaml)
        check_formulas(r, app["name"], yaml, templates, datasources, release=args.release, official=not args.no_official)
        reports.append(r)
    for rep in reports:
        rep.print()
    print("\nStatic checks only. Not yet proven in Studio: open the app, read App checker > Formulas, and walk the acceptance checks "
          "(docs/standards/powerfx-validation.md §6).")
    sys.exit(1 if any(rep.errors for rep in reports) else 0)


def latest_zips(cfg: dict) -> list[tuple[Path, bool]]:
    unmanaged, managed = zip_names(solution_identity(cfg))
    out = []
    for n, m in ((unmanaged, False), (managed, True)):
        p = dist_dir(cfg) / n
        if p.exists():
            out.append((p, m))
    return out


def cmd_validate(args: argparse.Namespace) -> None:
    cfg = load_config()
    targets = [(Path(p), Path(p).stem.endswith("_managed")) for p in args.zips] or latest_zips(cfg)
    if not targets:
        die("nothing to validate: run `uv run tools/pp.py build` first, or pass a ZIP path")
    reports = [validate_zip(p, cfg, m, roundtrip=not args.no_roundtrip) for p, m in targets]
    for rep in reports:
        rep.print()
    sys.exit(1 if any(rep.errors for rep in reports) else 0)


# --------------------------------------------------------------------------- settings

def cmd_settings(args: argparse.Namespace) -> None:
    cfg = load_config()
    zips = [p for p, m in latest_zips(cfg) if not m]
    if not zips:
        die("build first: the settings template is generated from the unmanaged ZIP")
    template = ROOT / "deployment" / "settings.template.json"
    template.parent.mkdir(exist_ok=True)
    run_pac(["solution", "create-settings", "--solution-zip", str(zips[0]), "--settings-file", str(template)], quiet=True)
    tpl = json.loads(read_text(template))
    print(f"Wrote {template.relative_to(ROOT)}")
    envs = [args.env] if args.env else list(cfg["environments"])
    bad = False
    for env in envs:
        bad |= not check_settings(cfg, env, tpl, strict=bool(args.env))
    sys.exit(1 if bad and args.env else 0)


def check_settings(cfg: dict, env: str, tpl: dict, strict: bool) -> bool:
    e = cfg["environments"].get(env)
    if not e:
        die(f"unknown environment '{env}' (pp.config.json environments)")
    path = ROOT / e["settings"]
    r = Report(f"Deployment settings: {env} ({e['settings']})")
    if not path.exists():
        r.error("file missing: copy deployment/settings.template.json and fill it in")
        r.print()
        return False
    s = json.loads(read_text(path))
    have_ev = {x["SchemaName"]: x.get("Value", "") for x in s.get("EnvironmentVariables", [])}
    have_cr = {x["LogicalName"]: x.get("ConnectionId", "") for x in s.get("ConnectionReferences", [])}
    for x in tpl.get("EnvironmentVariables", []):
        n = x["SchemaName"]
        if n not in have_ev:
            r.error(f"environment variable {n} missing")
        elif not have_ev[n]:
            (r.error if strict else r.warn)(f"environment variable {n} has no value")
    for x in tpl.get("ConnectionReferences", []):
        n = x["LogicalName"]
        if n not in have_cr:
            r.error(f"connection reference {n} missing")
        elif not have_cr[n]:
            (r.error if strict else r.warn)(f"connection reference {n} has no connection ID")
    extra = (set(have_ev) - {x["SchemaName"] for x in tpl.get("EnvironmentVariables", [])}) | \
            (set(have_cr) - {x["LogicalName"] for x in tpl.get("ConnectionReferences", [])})
    for n in sorted(extra):
        r.warn(f"{n} is not in the solution any more")
    if not r.errors and not r.warnings:
        r.ok("complete")
    r.print()
    return not r.errors


# --------------------------------------------------------------------------- import / export / check

def env_args(e: dict) -> list[str]:
    return ["--environment", e["url"]] if e.get("url") else []


def cmd_import(args: argparse.Namespace) -> None:
    cfg = load_config()
    e = cfg["environments"].get(args.env) or die(f"unknown environment '{args.env}'")
    managed = e.get("managed", False) if args.managed is None else args.managed
    zips = {m: p for p, m in latest_zips(cfg)}
    path = zips.get(managed) or die(f"no {'managed' if managed else 'unmanaged'} ZIP: run build first")
    rep = validate_zip(path, cfg, managed)
    if rep.errors:
        rep.print()
        die("the package fails validation")
    tpl_path = ROOT / "deployment" / "settings.template.json"
    run_pac(["solution", "create-settings", "--solution-zip", str(zips.get(False, path)), "--settings-file", str(tpl_path)], quiet=True)
    if not check_settings(cfg, args.env, json.loads(read_text(tpl_path)), strict=True):
        die(f"fill in {e['settings']} first")
    target = e.get("url") or "(the active pac auth profile's environment)"
    if e.get("confirm") and not args.yes:
        answer = input(f"Import {path.name} into {args.env.upper()} {target}? Type the environment name to confirm: ")
        if answer.strip().lower() != args.env.lower():
            die("not confirmed")
    cmd = ["solution", "import", "--path", str(path), "--settings-file", str(ROOT / e["settings"]), "--async"]
    cmd += env_args(e)
    if not managed:
        cmd.append("--publish-changes")
    if args.activate:
        cmd.append("--activate-plugins")
    if args.upgrade:
        cmd.append("--stage-and-upgrade")
    print(f"Importing {path.name} into {args.env} {target}")
    run_pac(cmd)


def cmd_export(args: argparse.Namespace) -> None:
    """Export the unmanaged solution from an environment and replace the source with it."""
    cfg = load_config()
    identity = solution_identity(cfg)
    if args.zip:
        # An unmanaged ZIP exported by hand from make.powerapps.com.
        zip_path = Path(args.zip).resolve()
        with zipfile.ZipFile(zip_path) as z:
            man = ET.fromstring(z.read("solution.xml")).find("SolutionManifest")
        if man.findtext("Managed") != "0":
            die("export the solution as Unmanaged: a managed ZIP cannot become source")
        if man.findtext("UniqueName") != identity["unique"]:
            die(f"the ZIP holds '{man.findtext('UniqueName')}', this project is '{identity['unique']}'")
    else:
        e = cfg["environments"].get(args.env) or die(f"unknown environment '{args.env}'")
        dist = dist_dir(cfg)
        (dist / "export").mkdir(parents=True, exist_ok=True)
        zip_path = dist / "export" / f"{identity['unique']}.zip"
        run_pac(["solution", "export", "--name", identity["unique"], "--path", str(zip_path), "--overwrite", *env_args(e)])
    src = src_dir(cfg)
    run_pac(["solution", "unpack", "--zipfile", str(zip_path), "--folder", str(src), "--packagetype", "Unmanaged",
             "--allowDelete", "true", "--allowWrite", "true", "--clobber", "true"], quiet=True)

    # Values never live in source (PA-T4): drop packaged current values.
    for v in src.glob("environmentvariabledefinitions/*/environmentvariablevalues.json"):
        print(f"Removed packaged value {v.relative_to(ROOT)} (values live in deployment settings)")
        v.unlink()
    # Flow env-var parameters carry the dev value as defaultValue on export (PA-T5): clear them.
    for f in (src / "Workflows").glob("*.json") if (src / "Workflows").exists() else []:
        flow = json.loads(read_text(f))
        changed = False
        for p in flow.get("properties", {}).get("definition", {}).get("parameters", {}).values():
            if (p.get("metadata") or {}).get("schemaName") and p.get("defaultValue") not in ("", None):
                p["defaultValue"] = ""
                changed = True
        if changed:
            write_text(f, json.dumps(flow, indent=2, ensure_ascii=False) + "\n")
    # Canvas apps: the .msapp becomes YAML source under canvas/; the build re-packs it.
    known = {a["name"]: a for a in cfg["canvasApps"]}
    for msapp in sorted((src / "CanvasApps").glob("*_DocumentUri.msapp")) if (src / "CanvasApps").exists() else []:
        name = msapp.name[: -len("_DocumentUri.msapp")]
        app = known.get(name)
        if not app:
            app = {"name": name, "source": f"canvas/{pascal(name.split('_', 1)[-1].rsplit('_', 1)[0]) or name}"}
            cfg["canvasApps"].append(app)
            print(f"New canvas app {name} -> {app['source']} (added to pp.config.json)")
        dest = ROOT / app["source"]
        with tempfile.TemporaryDirectory() as tmp:
            run_pac(["canvas", "unpack", "--msapp", str(msapp), "--sources", tmp, "--layout", "SourceCode"], quiet=True)
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(tmp, dest)
        msapr = next(dest.glob("*.msapr"), None)
        if msapr:
            msapr.rename(dest / f"{Path(app['source']).name}.msapr")
        msapp.unlink()
    save_config(cfg)
    print(f"\nSource updated from {args.zip or args.env}. Review `git diff`, then build and commit.")


def cmd_check(args: argparse.Namespace) -> None:
    cfg = load_config()
    zips = [p for p, m in latest_zips(cfg) if not m] or die("build first")
    out = dist_dir(cfg) / "checker"
    cmd = ["solution", "check", "--path", str(zips[0]), "--outputDirectory", str(out)]
    if cfg.get("checkerGeo"):
        cmd += ["--geo", cfg["checkerGeo"]]
    run_pac(cmd)
    print(f"Results in {out.relative_to(ROOT)}")


# --------------------------------------------------------------------------- main

def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")  # a console code page without § or an accent must not crash the report
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="check the toolchain").set_defaults(fn=cmd_doctor)

    s = sub.add_parser("setup", help="name the solution, publisher and app; regenerate IDs")
    s.add_argument("--client", required=True)
    s.add_argument("--project", required=True)
    s.add_argument("--code", required=True, help="project code, 2-6 letters (e.g. CON): AC IDs, file names")
    s.add_argument("--prefix", help="publisher prefix, 2-8 lowercase letters/digits (default: the code)")
    s.add_argument("--list-prefix", help="SharePoint list prefix (default: the code)")
    s.add_argument("--dev-env", help="Dev environment URL, for PROJECT.md and pp.config.json")
    s.add_argument("--dev-site", help="Dev SharePoint site URL, for PROJECT.md")
    s.add_argument("--solution-name", help="unique name (default: PascalCase client + project)")
    s.add_argument("--solution-display", help="display name (default: 'client project')")
    s.add_argument("--publisher-name", help="publisher unique name (default: keep)")
    s.add_argument("--publisher-display", help="publisher display name (default: keep)")
    s.add_argument("--app-name", help="canvas app display name (default: project)")
    s.add_argument("--force", action="store_true", help="allow renaming a solution past 1.0.0.0")
    s.set_defaults(fn=cmd_setup)

    s = sub.add_parser("bump", help="raise the solution version")
    s.add_argument("--part", choices=["major", "minor", "build", "revision"], default="build")
    s.add_argument("--set", help="exact four-part version")
    s.set_defaults(fn=cmd_bump)

    s = sub.add_parser("build", help="pack canvas apps and the solution, then validate")
    s.add_argument("--skip-canvas", action="store_true", help="leave the canvas apps out of the package")
    s.add_argument("--unmanaged-only", action="store_true")
    s.set_defaults(fn=cmd_build)

    s = sub.add_parser("fx", help="check the canvas source's formulas without packing (docs/standards/powerfx-validation.md)")
    s.add_argument("--release", action="store_true", help="also fail on TODO(AC stubs and mock data")
    s.add_argument("--no-official", action="store_true", help="skip Microsoft's parser (stdlib parser only)")
    s.set_defaults(fn=cmd_fx)

    s = sub.add_parser("validate", help="validate solution ZIPs (default: the latest build)")
    s.add_argument("zips", nargs="*")
    s.add_argument("--no-roundtrip", action="store_true", help="skip the pac solution unpack check")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("settings", help="regenerate the settings template and check each environment's file")
    s.add_argument("--env", help="check one environment strictly (every value filled)")
    s.set_defaults(fn=cmd_settings)

    s = sub.add_parser("import", help="import the built ZIP with the environment's deployment settings")
    s.add_argument("--env", required=True)
    g = s.add_mutually_exclusive_group()
    g.add_argument("--managed", dest="managed", action="store_true", default=None)
    g.add_argument("--unmanaged", dest="managed", action="store_false")
    s.add_argument("--activate", action="store_true", help="turn flows on after import")
    s.add_argument("--upgrade", action="store_true", help="stage and upgrade (removes components deleted from the solution)")
    s.add_argument("--yes", action="store_true", help="skip the confirmation for protected environments")
    s.set_defaults(fn=cmd_import)

    s = sub.add_parser("export", help="export the unmanaged solution from an environment into source")
    s.add_argument("--env", default="dev")
    s.add_argument("--zip", help="use an unmanaged ZIP exported by hand instead of calling pac solution export")
    s.set_defaults(fn=cmd_export)

    sub.add_parser("check", help="run the Power Apps solution checker (needs pac auth)").set_defaults(fn=cmd_check)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
