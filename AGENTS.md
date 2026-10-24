# Project architecture constraints

- Preserve all ten ObfuscationKernel architecture profiles. ObfuscationOS supplies
  userland for the same ten profiles (i386, x86_64, aarch64, arm32, rv64, rv32,
  loongarch64, mips, mips64, ppc); do not silently narrow either matrix.
- Use freestanding C++23 for the kernel and native extensions, with xmake as the
  build system. Project documentation, comments and identifiers are English.
- ObfuscationKernel owns core kernel mechanisms, native driver/module interfaces,
  essential platform support, the basic kernel GUI and kernel diagnostics.
- ObfuscationOS owns distribution policy, user programs, the system desktop,
  external kernel modules, external device drivers and Linux driver adaptation.
- ObfuscationOS consumes exported, architecture- and mode-specific Kernel SDK
  artifacts. Do not embed a kernel checkout or compile kernel source from the OS
  build. Keep artifact validation explicit; never choose arbitrary glob matches.
- Use concepts/templates and static dispatch for architecture-selected operations,
  scheduler policies and other measured hot paths. Keep runtime polymorphism at
  actual runtime device/module service boundaries; do not introduce a virtual
  interface just to share implementation.
- Keep model tests distinct from hardware execution and user-space integration
  tests. Metadata parsing is not code loading; process records are not isolation.
- Refactoring must preserve useful tests and move them with their implementation.
  Validate both the standalone kernel and its OS artifact consumer.

# Workspace rules

- This directory is the umbrella repository. `manifest.json` pins the component
  repositories; the components themselves are ignored here and have their own
  history. Run git inside a component, never at this root for component files.
- Work happens in paired worktrees under `wt/` (see `PLAN.md` and each
  component's `docs/PLAN.md`). A kernel worktree exports an SDK; its paired OS
  worktree points `--kernel_sdk` at it.
- Qualification receipts and prototype trees go to `ObfuscationEvidence/`. The
  `build` symlink points at its `archive/` so historical paths resolve; do not
  create new evidence there.
