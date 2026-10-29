#!/usr/bin/env python3
"""
Look things up in the Acies Power Apps reuse catalogue: the one list of existing canvas screens and components,
screen generators, named-formula sets, cloud flows, list schemas and shared code worth reusing (its repository is
in tools/catalogue.config.json).

  uv run tools/catalogue.py fetch                        clone or update it in references/_catalogue/
  uv run tools/catalogue.py list [--format md|json]      every entry (json: in full)
  uv run tools/catalogue.py search <words…> [--top N]    entries matching the words, best first

`search` matches words, not meaning: a miss doesn't prove nothing fits. Skills read `list` in full.
Standard library only; git must be able to read the repository (`gh auth setup-git` if it can't).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path(__file__).with_name("catalogue.config.json")
CLONE = ROOT / "references" / "_catalogue"


def config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def fetch() -> int:
    cfg = config()
    if (CLONE / ".git").exists():
        r = git("pull", "--ff-only", "--quiet", cwd=CLONE)
    else:
        CLONE.parent.mkdir(parents=True, exist_ok=True)
        r = git("clone", "--depth", "1", "--branch", cfg["branch"], "--quiet", cfg["repository"], str(CLONE))
    if r.returncode != 0:
        print(f"Couldn't read the catalogue at {cfg['repository']}:\n{r.stderr.strip()}\n"
              "Check you have read access to it, and that git can use your GitHub sign-in (gh auth setup-git).")
        return 1
    sha = git("rev-parse", "--short", "HEAD", cwd=CLONE).stdout.strip()
    print(f"Catalogue @ {sha}: {len(entries())} entries in {CLONE.relative_to(ROOT)}.")
    return 0


def entries():
    if not (CLONE / "entries").exists():
        sys.exit("No catalogue here yet: run python tools/catalogue.py fetch")
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((CLONE / "entries").glob("*.json"))]


def _chain(e) -> str:
    tool = e.get("toolchain") or {}
    return f"{tool['pac']} / {tool['studio']}" if tool.get("pac") and tool.get("studio") else "—"


def _row(e) -> str:
    cell = lambda v: str(v or "").replace("|", "\\|")
    return (f"| `{e.get('id')}` | {e.get('type')} | {cell(e.get('name'))} | {cell(e.get('summary'))} | {e.get('status')} "
            f"| {e.get('reuse', {}).get('rights')} | {_chain(e)} | {cell(', '.join(e.get('keywords', [])))} |")


HEADER = "| Entry | Type | Name | What it does | Status | Rights | pac / Studio | Keywords |\n|---|---|---|---|---|---|---|---|"


def show(rows, fmt: str):
    if fmt == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    elif rows:
        print(HEADER)
        for e in rows:
            print(_row(e))
    else:
        print("No entries.")


def search(words, top: int, pool=None):
    terms = [w.lower() for w in words if len(w) > 2]
    weights = (("keywords", 3), ("name", 3), ("capabilities", 2), ("summary", 1), ("type", 1))
    scored = []
    for e in (entries() if pool is None else pool):
        if e.get("status") == "Deprecated":
            continue
        score = 0
        for key, weight in weights:
            text = " ".join(e[key]) if isinstance(e.get(key), list) else str(e.get(key, ""))
            text = text.lower()
            score += weight * sum(1 for t in terms if re.search(rf"\b{re.escape(t)}", text))
        if score:
            scored.append((score, e))
    scored.sort(key=lambda s: -s[0])
    return [e for _, e in scored[:top]]


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch")
    ls = sub.add_parser("list")
    ls.add_argument("--format", choices=["md", "json"], default="md")
    s = sub.add_parser("search")
    s.add_argument("words", nargs="+")
    s.add_argument("--top", type=int, default=10)
    s.add_argument("--format", choices=["md", "json"], default="md")
    args = ap.parse_args(argv)
    if args.cmd == "fetch":
        return fetch()
    show(entries() if args.cmd == "list" else search(args.words, args.top), args.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
