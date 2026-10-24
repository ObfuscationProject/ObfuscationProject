#!/usr/bin/env python3
"""Synchronise component repositories with manifest.json.

  sync.py            clone missing components, fetch, check out pinned commits
  sync.py --pin      rewrite manifest.json from each component's current HEAD
  sync.py --status   print pinned vs current commit for each component
  sync.py --latest   check out each component's origin/main instead of the pin
  sync.py --validate check the manifest structure without touching checkouts
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.json"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pin", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    components = manifest["components"]

    if args.validate:
        problems = []
        for name, c in components.items():
            for key in ("url", "branch", "commit"):
                if key not in c:
                    problems.append(f"{name}: missing {key}")
            if not c.get("url", "").startswith("https://github.com/ObfuscationProject/"):
                problems.append(f"{name}: unexpected url")
            if len(c.get("commit", "")) != 40:
                problems.append(f"{name}: commit is not a full SHA")
        for problem in problems:
            print(problem)
        print(f"manifest: {len(components)} components, {'ok' if not problems else 'INVALID'}")
        return 1 if problems else 0

    if args.pin:
        for name, c in components.items():
            repo = ROOT / name
            c["commit"] = git(repo, "rev-parse", "HEAD")
            c["branch"] = git(repo, "branch", "--show-current") or c.get("branch", "")
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"pinned {len(components)} components")
        return 0

    rc = 0
    for name, c in components.items():
        repo = ROOT / name
        if not repo.exists():
            if args.status:
                print(f"{name}: missing"); rc = 1; continue
            subprocess.run(["git", "clone", c["url"], str(repo)], check=True)
        if args.status:
            head = git(repo, "rev-parse", "HEAD")
            mark = "ok" if head == c["commit"] else "DIFFERS"
            print(f"{name}: pinned {c['commit'][:12]} current {head[:12]} {mark}")
            rc |= head != c["commit"]
            continue
        subprocess.run(["git", "-C", str(repo), "fetch", "--tags", "origin"], check=True)
        if git(repo, "status", "--porcelain"):
            print(f"{name}: working tree dirty, not checking out {c['commit'][:12]}", file=sys.stderr)
            rc = 1
            continue
        target = "origin/main" if args.latest else c["commit"]
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", "--detach", target], check=True)
        print(f"{name}: {git(repo, 'rev-parse', '--short=12', 'HEAD')} ({'origin/main' if args.latest else c.get('branch', '')})")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
