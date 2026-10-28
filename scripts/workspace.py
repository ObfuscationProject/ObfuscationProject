#!/usr/bin/env python3
"""Workspace meta commands. Nothing is built here; each command runs xmake inside
a component repository.

  workspace.py sdk-all    [-a ARCH] [-m MODE] [--systoolchain-dir DIR] [--qemu-dir DIR]
  workspace.py distro-all [-a ARCH] [-m MODE] [--systoolchain-dir DIR]
  workspace.py matrix     [-m MODE] [--systoolchain-dir DIR] [--qemu-dir DIR]
  workspace.py cross-tests [-a ARCH] [-m MODE]

cross-tests runs the OS suites that compare the SDK consumer with the kernel
checkout itself (they skip in the OS CI, which has only the SDK artifact); sdk-all
must have exported the SDK first. distro-all and matrix run them too.

A root xmake.lua is deliberately absent: xmake resolves the project directory
to the outermost ancestor that holds an xmake.lua, so a workspace-level
xmake.lua would hijack every component build.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KERNEL = ROOT / "ObfuscationKernel"
OS = ROOT / "ObfuscationOS"
FAST_LANE = [
    {"arch": "x86_64", "triple": "x86_64-elf", "qemu": "qemu-system-x86_64"},
    {"arch": "arm32", "triple": "arm-none-eabi", "qemu": "qemu-system-arm"},
    {"arch": "ppc", "triple": "powerpc-eabi", "qemu": "qemu-system-ppc"},
]
TRIPLES = {"i386": "i386-elf", "aarch64": "aarch64-elf", "rv64": "riscv64-elf", "rv32": "riscv32-elf",
           "loongarch64": "loongarch64-elf", "mips": "mips-elf", "mips64": "mips64-elf"}
TRIPLES.update({l["arch"]: l["triple"] for l in FAST_LANE})
QEMUS = {"i386": "qemu-system-i386", "aarch64": "qemu-system-aarch64", "rv64": "qemu-system-riscv64",
         "rv32": "qemu-system-riscv32", "loongarch64": "qemu-system-loongarch64", "mips": "qemu-system-mips",
         "mips64": "qemu-system-mips64"}
QEMUS.update({l["arch"]: l["qemu"] for l in FAST_LANE})


def xmake(repo: Path, *argv: str) -> None:
    print(f"[{repo.name}] xmake {' '.join(argv)}", flush=True)
    subprocess.run(["xmake", *argv], cwd=repo, check=True)


def configure_kernel(args, arch: str) -> None:
    argv = ["f", "-y", "-m", args.mode, "-a", arch]
    if args.systoolchain_dir:
        argv.append(f"--systoolchain_dir={Path(args.systoolchain_dir).resolve() / TRIPLES[arch]}")
    if getattr(args, "qemu_dir", None):
        argv.append(f"--qemu_binary={Path(args.qemu_dir).resolve() / QEMUS[arch]}")
    xmake(KERNEL, *argv)


def configure_os(args, arch: str) -> None:
    argv = ["f", "-y", "-m", args.mode, "-a", arch,
            f"--kernel_sdk={KERNEL / 'build' / 'sdk' / arch / args.mode}"]
    if args.systoolchain_dir:
        argv.append(f"--systoolchain_dir={Path(args.systoolchain_dir).resolve() / TRIPLES[arch]}")
    xmake(OS, *argv)


def sdk_all(args, arch: str) -> None:
    configure_kernel(args, arch)
    xmake(KERNEL, "-y", "-b", "okernel")
    xmake(KERNEL, "test")
    xmake(KERNEL, "-y", "-b", "kernel-sdk")


def cross_tests(args, arch: str) -> None:
    tools = OS / "tests" / "tools"
    modules = sorted(p.stem for p in tools.glob("test_*.py") if "import kernel_checkout" in p.read_text())
    if not modules:
        raise SystemExit("no OS suite imports tests/tools/kernel_checkout.py")
    env = dict(os.environ, OK_REQUIRE_KERNEL_CHECKOUT="1", OK_KERNEL_CHECKOUT=str(KERNEL),
               OK_TEST_KERNEL_SDK=str(KERNEL / "build" / "sdk" / arch / args.mode),
               OK_TEST_KERNEL_ARCH=arch, OK_TEST_KERNEL_MODE=args.mode, PYTHONDONTWRITEBYTECODE="1")
    print(f"[{OS.name}] cross-tests: {' '.join(modules)}", flush=True)
    subprocess.run([sys.executable, "-B", "-m", "unittest", *modules], cwd=tools, env=env, check=True)


def distro_all(args, arch: str, boot: bool = True) -> None:
    configure_os(args, arch)
    for target in ("kernel-sdk-check", "uapi-test", "libc-test", "distro_image", "rootfs-ext4"):
        xmake(OS, "-y", "-b", target)
    cross_tests(args, arch)
    if boot:
        xmake(OS, "qemu-distro", "--fs=ext4", "--require-native", "--timeout=30")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("sdk-all", "distro-all", "matrix", "cross-tests"):
        p = sub.add_parser(name)
        if name != "matrix":
            p.add_argument("-a", "--arch", default="x86_64")
        p.add_argument("-m", "--mode", default="debug", choices=["debug", "release"])
        p.add_argument("--systoolchain-dir", help="directory holding one SysToolchain installation per triple")
        p.add_argument("--qemu-dir", help="directory holding host qemu-system-* executables")
    args = ap.parse_args()
    if args.cmd == "sdk-all":
        sdk_all(args, args.arch)
    elif args.cmd == "distro-all":
        distro_all(args, args.arch)
    elif args.cmd == "cross-tests":
        cross_tests(args, args.arch)
    else:
        failed = []
        for lane in FAST_LANE:
            try:
                sdk_all(args, lane["arch"])
                distro_all(args, lane["arch"], boot=False)
            except subprocess.CalledProcessError:
                failed.append(lane["arch"])
        if failed:
            print("fast lane failed for: " + ", ".join(failed), file=sys.stderr)
            return 1
        print("fast lane passed: " + ", ".join(l["arch"] for l in FAST_LANE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
