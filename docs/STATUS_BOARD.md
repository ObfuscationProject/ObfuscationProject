# ObfuscationProject module board

Generated 2026-10-25T20:54:23+00:00 from ObfuscationOS@efe405e7e5a8, ObfuscationKernel@20ec30a23e25, SysToolchain@01660933bca5, ObfuscationProject@666a1f766868, ObfuscationEvidence@3be882f85ab5.

State is the declared judgement from the plans; presence counts declared paths found on main; checks are hosted commands (run).

| 计划 (planned) | 脚手架 (scaffold) | 模型 (model) | 有界 (bounded) | 原生 (native) | 稳定 (stable) |
| --- | --- | --- | --- | --- | --- |
| 7 | 8 | 3 | 14 | 8 | 4 |

## 用户会话 · OS · 非特权进程

| Module | Tag | State | Presence | Checks | Plan | Summary |
| --- | --- | --- | --- | --- | --- | --- |
| Wayland compositor | 新增 | 计划 | — | — | feat/compositor | libwayland、xdg-shell、wl_shm、pixman 软渲染；独立进程 |
| greeter · 面板 · 通知 | 新增 | 计划 | — | — | feat/compositor | 受限会话；崩溃不影响 compositor |
| Terminal · Files · Editor · Settings · Tasks · Logs | 迁移 | 有界 | 2/2 | — | feat/desktop-apps | 今天是 system-gui 内核态视图；目标是走 Wayland + PTY 的独立进程 |
| 包管理 · 安装器 · 恢复 | 新增 | 计划 | — | — | feat/packages-installer | 包格式、仓库、回滚、恢复镜像 |

## 系统服务 · OS · PID 1 监督

| Module | Tag | State | Presence | Checks | Plan | Summary |
| --- | --- | --- | --- | --- | --- | --- |
| init / PID 1 + 服务图 | 不变 | 有界 | 3/3 | — | feat/services-complete | 监督、控制、quiesce；改用 musl 构建 |
| logd · timed · resolved · login | 不变 | 有界 | 4/4 | — | feat/net-services | 现有；resolver 升级为 DNS |
| netd · dhcpc · sntp | 新增 | 计划 | — | — | feat/net-services | 接口配置、路由、名字、时间 |
| devd · seatd · sessiond | 新增 | 计划 | — | — | feat/services-complete | 设备代理、座位租约、会话切换 |
| 通用关机 | 升级 | 有界 | 3/3 | — | feat/services-complete | ACPI / PSCI / SBI / 板级 ×10，取代 x86_64 专用后端 |

## 用户库 · OS

| Module | Tag | State | Presence | Checks | Plan | Summary |
| --- | --- | --- | --- | --- | --- | --- |
| musl 1.2.5 静态 + 共享 + ld.so | 升级 | 脚手架 | 3/3 | 1/1 pass | feat/musl-primary | 主 libc；TLS、dlopen、pthread 取消 ×10 |
| libstdc++ (hosted) · FreeType · HarfBuzz | 新增 | 计划 | — | — | feat/shared-musl-loader | 应用与工具包依赖；UTF-8 / CJK |
| POSIX sh + toybox/busybox | 新增 | 脚手架 | 2/2 | — | feat/musl-primary | 脚本、展开、作业控制、coreutils 广度；许可证决策待定 |
| okcrt | 收缩 | 原生 | 2/2 | — | docs/decisions/0001 | 仅 init 引导与救援工具 |

## OS 内核态模块 · 真正可加载 · ABI N

| Module | Tag | State | Presence | Checks | Plan | Summary |
| --- | --- | --- | --- | --- | --- | --- |
| virtio-blk · virtio-net · virtio-rng | 升级 | 有界 | 3/3 | — | feat/drivers-as-modules | 从静态链接变为 ELF 重定位加载的 .okmod；IRQ 完成 |
| virtio-gpu · virtio-input · ramfb · PS/2 · USB HID | 迁移 | 脚手架 | 2/2 | — | feat/display-input-drivers | 从内核 driver/ 迁到 OS，经 display / input UAPI 暴露 |
| linux-driver-compat | 升级 | 模型 | 2/2 | — | P4 | 一个选定 Linux 版本、一个选定驱动的真实后端 |
| boot：OKAR 救援根、挂载策略 | 不变 | 原生 | 3/3 | — | — | 现有 |

## Kernel SDK 边界 · ABI / UAPI / manifest

| Module | Tag | State | Presence | Checks | Plan | Summary |
| --- | --- | --- | --- | --- | --- | --- |
| Kernel SDK 边界 | 升级 | 稳定 | 2/2 | — | chore/sdk75-consumer | ABI 74 / UAPI 0.16.0 今天；目标 ABI 75+ / UAPI 0.17+（display.h、input.h、模块加载 ABI）；manifest 哈希 admission；umbrella manifest 钉五个组件 SHA |

## 系统调用层 · Kernel

| Module | Tag | State | Presence | Checks | Plan | Summary |
| --- | --- | --- | --- | --- | --- | --- |
| Linux personality ×10 | 升级 | 有界 | 2/2 | — | feat/musl-primary | musl 的主路径；覆盖 POSIX.1-2024 选定 profile |
| 原生 UAPI | 收缩 | 原生 | 2/2 | — | docs/decisions/0001 | init、救援、诊断 |
| display / input / seat UAPI | 新增 | 脚手架 | 2/2 | 1/1 pass | feat/display-input-uapi | dumb buffer、scanout、vsync、设备租约；草案头文件版本 0 |
| KernelExtension | 收缩 | 原生 | 1/1 | — | feat/compositor | 仅 boot 挂载钩子；桌面回调移除 |

## 内核服务 · Kernel

| Module | Tag | State | Presence | Checks | Plan | Summary |
| --- | --- | --- | --- | --- | --- | --- |
| sched | 升级 | 有界 | 2/2 | — | feat/smp-bringup | per-CPU 运行队列、SMP、IPI、CPU 时间统计 |
| process · signals · futex | 不变 | 原生 | 2/2 | 1/1 pass | refactor/user-runtime-split | 现有机制，拆到 user/{loader,entry,vm,wait,signals} |
| TTY | 新增 | 有界 | 2/2 | — | feat/tty-jobctl | 原始 PTY 对已存在；termios、N_TTY、控制终端、devpts 待做 |
| sockets | 升级 | 有界 | 3/3 | — | feat/net-core | UNIX + INET + INET6；通用就绪 API |
| 模块加载器 | 新增 | 模型 | 1/1 | — | feat/module-loader | ELF 重定位 ×10、符号表、引用计数、拒绝卸载；今天只有元数据解析 |
| 救援 GUI + 诊断 shell | 收缩 | 原生 | 2/2 | — | refactor/user-runtime-split | src/rescue/，仅 kernel_gui 构建 |

## 存储与网络 · Kernel

| Module | Tag | State | Presence | Checks | Plan | Summary |
| --- | --- | --- | --- | --- | --- | --- |
| VFS | 升级 | 原生 | 2/2 | — | feat/storage-durable | dentry / inode / mount 引用、页缓存、文件锁、挂载变更 |
| ext4 | 升级 | 有界 | 3/3 | 1/1 pass | feat/storage-durable | 默认 journalled、htree、extent 增长、符号链接、metadata_csum；合并为 fs/ext4/ 八个头 |
| FAT · OKAR | 不变 | 有界 | 2/2 | — | — | 现有 |
| block | 升级 | 有界 | 2/2 | — | feat/irq-wait-time | 请求队列、IRQ 完成、回写 |
| net core | 升级 | 有界 | 2/2 | — | feat/net-core | eth / ARP / ND、IPv4 / IPv6、ICMP、UDP、通用 TCP、路由 |

## 平台 · Kernel

| Module | Tag | State | Presence | Checks | Plan | Summary |
| --- | --- | --- | --- | --- | --- | --- |
| mm | 升级 | 脚手架 | 4/4 | 2/2 pass | feat/mm-general | 真实内存图、运行期帧分配器、slab、VM / COW、配额、回收 |
| irq | 新增 | 脚手架 | 2/2 | 1/1 pass | feat/irq-wait-time | 控制器 ×10、IRQ 驱动唤醒、工作队列 |
| time | 升级 | 脚手架 | 2/2 | — | feat/irq-wait-time | 校准时钟、POSIX 定时器 |
| smp | 新增 | 模型 | 2/2 | — | feat/smp-bringup | AP 启动、TLB shootdown、锁级别（先 x86_64 / aarch64 / rv64） |
| boot | 升级 | 有界 | 2/2 | — | feat/mm-general | FDT / ACPI / E820 发现进入 kernel_main |
| display / input 机制 | 新增 | 计划 | — | — | feat/display-input-uapi | 缓冲对象、scanout、输入事件队列、座位租约 |

## 架构后端 ×10 · 静态分派

| Module | Tag | State | Presence | Checks | Plan | Summary |
| --- | --- | --- | --- | --- | --- | --- |
| i386 · x86_64 · aarch64 · arm32 · rv64 · rv32 · loongarch64 · mips · mips64 · ppc | 不变 | 原生 | 10/10 | — | — | 不变；每个架构新增 irq 控制器、AP 启动（可用者）、signal.hpp 单文件 |

## 工具链与工程

| Module | Tag | State | Presence | Checks | Plan | Summary |
| --- | --- | --- | --- | --- | --- | --- |
| SysToolchain · ObfuscationRepo | 不变 | 稳定 | 1/1 | 1/1 pass | PLAN.md | 不变；CI 消费预编译发布件（等 v0.1.0 发布完成） |
| umbrella 仓库 + manifest | 新增 | 稳定 | 3/3 | 1/1 pass | — | 钉五个 SHA；工作区脚本；状态看板 |
| ObfuscationEvidence | 新增 | 稳定 | 2/2 | — | PLAN.md | 证据与鉴定工具按分支@SHA 归档 |
| ledger → 能力矩阵 | 新增 | 脚手架 | 3/3 | — | P0 | 文档与 _POSIX_* 策略由 ledger.json 生成 |
