#!/usr/bin/env python3
"""Create a paired kernel/OS worktree under wt/.

  wt_pair.py --topic mm-general [--kind feat|refactor|chore|fix|docs] [--base-branch main]
             [--os-topic NAME] [--os-kind KIND] [--kernel-only | --os-only]

Creates wt/kernel-<topic> (branch <kind>/<topic>) and wt/os-<os-topic> (branch
<os-kind>/<os-topic>, defaulting to the kernel topic and kind) from the base
branch of each component, and prints the configure commands that bind the OS
worktree to the kernel worktree's SDK export.

  wt_pair.py --topic storage-durable --os-topic mkfs-e2fsprogs --os-kind fix
"""
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def add(repo: str, path: Path, branch: str, base: str) -> None:
    existing = subprocess.run(["git", "-C", str(ROOT / repo), "branch", "--list", branch],
                              capture_output=True, text=True).stdout.strip()
    if path.exists():
        print(f"{path} exists, skipping")
        return
    argv = ["git", "-C", str(ROOT / repo), "worktree", "add", str(path)]
    argv += [branch] if existing else ["-b", branch, base]
    subprocess.run(argv, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--kind", default="feat", choices=["feat", "refactor", "chore", "fix", "docs"])
    ap.add_argument("--base-branch", default="main")
    ap.add_argument("--os-topic", help="OS worktree topic when it differs from the kernel's")
    ap.add_argument("--os-kind", choices=["feat", "refactor", "chore", "fix", "docs"],
                    help="OS branch kind when it differs from the kernel's")
    ap.add_argument("--kernel-only", action="store_true")
    ap.add_argument("--os-only", action="store_true")
    ap.add_argument("--arch", default="x86_64")
    args = ap.parse_args()
    os_topic = args.os_topic or args.topic
    os_kind = args.os_kind or args.kind
    (ROOT / "wt").mkdir(exist_ok=True)
    k = ROOT / "wt" / f"kernel-{args.topic}"
    o = ROOT / "wt" / f"os-{os_topic}"
    if not args.os_only:
        add("ObfuscationKernel", k, f"{args.kind}/{args.topic}", args.base_branch)
    if not args.kernel_only:
        add("ObfuscationOS", o, f"{os_kind}/{os_topic}", args.base_branch)
    print("\nNext:")
    if not args.os_only:
        print(f"  (cd {k} && xmake f -y -m debug -a {args.arch} && xmake -y -b kernel-sdk)")
    if not args.kernel_only:
        sdk = (k if not args.os_only else ROOT / "ObfuscationKernel") / "build" / "sdk" / args.arch / "debug"
        print(f"  (cd {o} && xmake f -y -m debug -a {args.arch} --kernel_sdk={sdk} && xmake -y -b kernel-sdk-check)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
