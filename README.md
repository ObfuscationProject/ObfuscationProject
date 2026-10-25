# ObfuscationProject workspace

Umbrella repository for the Obfuscation operating system project. It pins the
component repositories in `manifest.json`, provides workspace-level scripts
and holds the cross-component plan. It contains no product source.

| Component | Role |
| --- | --- |
| [ObfuscationKernel](https://github.com/ObfuscationProject/ObfuscationKernel) | Multi-architecture freestanding C++23 kernel; exports the Kernel SDK |
| [ObfuscationOS](https://github.com/ObfuscationProject/ObfuscationOS) | Distribution: userland, PID 1, drivers, desktop, rootfs; consumes the SDK |
| [SysToolchain](https://github.com/ObfuscationProject/SysToolchain) | Reproducible GCC/Binutils/QEMU builds for ten targets |
| [ObfuscationRepo](https://github.com/ObfuscationProject/ObfuscationRepo) | xmake package repository (`systoolchain`) |
| [ObfuscationEvidence](https://github.com/ObfuscationProject/ObfuscationEvidence) | Qualification receipts, status snapshots, frozen history |

## Set up

```sh
git clone https://github.com/ObfuscationProject/ObfuscationProject.git
cd ObfuscationProject
python3 scripts/sync.py            # clone/fetch components and check out the pinned commits
python3 scripts/workspace.py sdk-all -a x86_64      # build, test and export the kernel SDK
python3 scripts/workspace.py distro-all -a x86_64   # build the OS consumer against it and boot it in QEMU
```

`python3 scripts/sync.py --pin` rewrites `manifest.json` from the components'
current HEADs. `python3 scripts/workspace.py matrix` runs the three-architecture
fast lane (x86_64, arm32, ppc) across kernel and OS. `python3 scripts/workspace.py
cross-tests -a ARCH` runs the OS suites that compare the SDK consumer with the
kernel checkout itself; OS CI skips them because it has only the SDK artifact. `python3 scripts/wt_pair.py
--topic NAME` creates a paired kernel/OS worktree under `wt/`.

Local toolchains: pass `--systoolchain-dir DIR` (one installation per triple) to
the workspace commands, or let each component resolve the `systoolchain` package
from ObfuscationRepo.

There is deliberately no `xmake.lua` at this level: xmake resolves the project
directory to the outermost ancestor holding an `xmake.lua`, so a workspace-level
file would hijack every component build.

## Module board

`status/modules.json` lists every module of the target architecture with its
layer, tag (new / upgrade / move / shrink / keep), declared state (planned,
scaffold, model, bounded, native, stable), the paths that must exist on each
component's main and the hosted checks that must pass. `python3
scripts/status_board.py --run-checks` measures presence and runs the checks, then
writes `docs/index.html`, `docs/STATUS_BOARD.md` and `docs/status.json`. The
`status-board` workflow regenerates them on every push and every six hours, and
GitHub Pages serves `docs/` as the live board. Changing a module's state is a
one-line edit to the JSON, reviewed like code.

## Plan

`PLAN.md` holds the workspace-level phases and dependency graph; each component
has its own `PLAN.md` (`docs/PLAN.md` in the kernel and OS).
