# ObfuscationProject workspace

Umbrella repository for the Obfuscation operating system project. It pins the
component repositories in `manifest.json`, provides workspace-level xmake tasks
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
xmake sdk-all --arch=x86_64        # export the kernel SDK for one architecture
xmake distro-all --arch=x86_64     # build the OS consumer against it and boot it in QEMU
```

`python3 scripts/sync.py --pin` rewrites `manifest.json` from the components'
current HEADs. `xmake matrix` runs the three-architecture fast lane (x86_64,
arm32, ppc) across kernel and OS. `xmake wt-pair --topic=NAME` creates a paired
kernel/OS worktree under `wt/`.

Local toolchains: pass `--systoolchain_dir=DIR` to the tasks, or let each
component resolve the `systoolchain` package from ObfuscationRepo.

## Plan

`PLAN.md` holds the workspace-level phases and dependency graph; each component
has its own `PLAN.md` (`docs/PLAN.md` in the kernel and OS).
