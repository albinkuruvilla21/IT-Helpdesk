"""reset_template: turn a delivered project back into the clean Acies Power Apps template.

    uv run tools/reset_template.py                 dry run: lists what would be removed and restored
    uv run tools/reset_template.py --apply         does it
    uv run tools/reset_template.py --ref <git ref> restore the starter files from another commit or tag (default: tag template-starter)

WHAT IT REMOVES (everything that belongs to one client project)
  canvas/<every app>        solution/src            deployment/settings.dev|test|prod|template.json     dist/
  schemas/*.csv             specs/ (all but README.md and acceptance-criteria/.gitkeep)
  inputs/ (all but README.md and the .gitkeep files)            specs/_working, tools/_working
  tools/build_*.py          the project's generators: MOVED to tools/examples/<name>.example.py (worked examples), not deleted
WHAT IT RESTORES from the starter commit (tag template-starter): canvas/StarterApp, solution/src (starter solution, sample flow, variables),
  deployment/settings.*.json, pp.config.json, PROJECT.md, specs/README.md, schemas/README.md, inputs/README.md and the .gitkeep files.
WHAT IT KEEPS: tools (pp.py, canvas_ui.py, powerfx.py, tests, ...), docs (standards, traps, lessons), .claude/skills, samples, CLAUDE.md, README.md,
  PROMPTS.md. CHANGELOG.md is not touched: replace the project's entries by hand with one template entry.
It never commits, never touches git history, and refuses to run with uncommitted changes unless --force is given.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "template-starter"
APPLY, FORCE = "--apply" in sys.argv, "--force" in sys.argv

KEEP_FILES = {"specs": {"README.md"}, "inputs": {"README.md"}, "schemas": {"README.md", "import-lists.console.js"}}
RESTORE = ["canvas/StarterApp", "solution/src", "deployment/settings.dev.json", "deployment/settings.test.json", "deployment/settings.prod.json",
           "pp.config.json", "PROJECT.md", "README.md", "specs/README.md", "specs/acceptance-criteria/.gitkeep", "inputs/README.md", "inputs/branding/.gitkeep",
           "inputs/brd/.gitkeep", "inputs/design/.gitkeep", "inputs/other/.gitkeep", "inputs/transcripts/.gitkeep", "schemas/README.md"]


def git(*a, check=True):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=check).stdout


def rm(path: Path):
    print("  remove ", path.relative_to(ROOT))
    if APPLY:
        shutil.rmtree(path) if path.is_dir() else path.unlink()


def main() -> int:
    if git("rev-parse", "--verify", REF, check=False).strip() == "":
        print(f"The starter ref '{REF}' does not exist. Give --ref <commit or tag> that holds the clean template's starter files.")
        return 2
    if git("status", "--porcelain").strip() and not FORCE:
        print("There are uncommitted changes. Commit or stash them first (or pass --force).")
        return 2
    print(("APPLYING" if APPLY else "DRY RUN") + f" against starter ref {REF}\n")
    for app in sorted((ROOT / "canvas").glob("*")):
        rm(app)
    for p in [ROOT / "solution" / "src", ROOT / "dist"]:
        if p.exists():
            rm(p)
    for z in sorted((ROOT / "releases").glob("*.zip")):  # the project's releases; releases/README.md stays
        rm(z)
    for env in ("dev", "test", "prod", "template"):  # settings.template.json is made by a project (G11), not by the starter
        f = ROOT / "deployment" / f"settings.{env}.json"
        if f.exists():
            rm(f)
    for folder, keep in KEEP_FILES.items():
        base = ROOT / folder
        for item in sorted(base.glob("*")) if base.exists() else []:
            if item.name in keep or item.name == "acceptance-criteria" and folder == "specs":
                continue
            if folder == "inputs" and item.is_dir():
                for sub in sorted(item.rglob("*"), reverse=True):
                    if sub.is_file() and sub.name != ".gitkeep":
                        rm(sub)
                continue
            if item.name == ".gitkeep":
                continue
            rm(item)
    ac = ROOT / "specs" / "acceptance-criteria"
    for f in sorted(ac.glob("*")) if ac.exists() else []:
        if f.name != ".gitkeep":
            rm(f)
    for extra in (ROOT / "tools" / "_working",):
        if extra.exists():
            rm(extra)
    ex = ROOT / "tools" / "examples"
    for gen in sorted((ROOT / "tools").glob("build_*.py")):
        target = ex / (gen.stem.replace("build_", "") + ".example.py")
        print("  move   ", gen.relative_to(ROOT), "->", target.relative_to(ROOT))
        if APPLY:
            ex.mkdir(exist_ok=True)
            gen.replace(target)
    print()
    for path in RESTORE:
        print("  restore", path)
        if APPLY:
            git("checkout", REF, "--", path)
    print("\nNext: uv run tools/pp.py doctor; uv run tools/pp.py build; uv run python -m unittest discover -s tools/tests; then edit CHANGELOG.md and commit.")
    if not APPLY:
        print("(dry run: nothing was changed; pass --apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
