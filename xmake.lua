set_project("ObfuscationProject")
set_version("0.1.0")

-- Workspace meta tasks. Nothing is built here; each task runs xmake inside a
-- component repository. The evidence archive is reachable through the `build`
-- symlink, so this project never writes a build directory of its own.
set_config("builddir", ".out")

local components = {kernel = "ObfuscationKernel", os = "ObfuscationOS"}
local fast_lane = {
    {arch = "x86_64", triple = "x86_64-elf", qemu = "qemu-system-x86_64"},
    {arch = "arm32", triple = "arm-none-eabi", qemu = "qemu-system-arm"},
    {arch = "ppc", triple = "powerpc-eabi", qemu = "qemu-system-ppc"},
}

local function component_dir(name)
    return path.join(os.projectdir(), components[name])
end

local function run_in(dir, argv)
    print("[" .. path.filename(dir) .. "] xmake " .. table.concat(argv, " "))
    local ok = os.execv("xmake", argv, {curdir = dir, try = true}) == 0
    if not ok then raise("xmake %s failed in %s", table.concat(argv, " "), dir) end
end

local function toolchain_args(opt, triple)
    local args = {}
    if opt.get("systoolchain_dir") then
        table.insert(args, "--systoolchain_dir=" .. path.absolute(path.join(opt.get("systoolchain_dir"), triple)))
    end
    return args
end

local function configure_kernel(opt, lane, mode)
    local argv = {"f", "-y", "-m", mode, "-a", lane.arch}
    for _, a in ipairs(toolchain_args(opt, lane.triple)) do table.insert(argv, a) end
    if opt.get("qemu_dir") then
        table.insert(argv, "--qemu_binary=" .. path.join(opt.get("qemu_dir"), lane.qemu))
    end
    run_in(component_dir("kernel"), argv)
end

local function configure_os(opt, lane, mode)
    local sdk = path.join(component_dir("kernel"), "build", "sdk", lane.arch, mode)
    local argv = {"f", "-y", "-m", mode, "-a", lane.arch, "--kernel_sdk=" .. sdk}
    for _, a in ipairs(toolchain_args(opt, lane.triple)) do table.insert(argv, a) end
    run_in(component_dir("os"), argv)
end

local function lane_for(arch)
    for _, lane in ipairs(fast_lane) do if lane.arch == arch then return lane end end
    return {arch = arch, triple = arch .. "-elf", qemu = "qemu-system-" .. arch}
end

local common_options = {
    {"a", "arch", "kv", "x86_64", "Architecture profile"},
    {"m", "mode", "kv", "debug", "debug or release"},
    {nil, "systoolchain_dir", "kv", nil, "Directory containing one SysToolchain installation per triple"},
    {nil, "qemu_dir", "kv", nil, "Directory containing host qemu-system-* executables"},
}

task("sdk-all")
    set_menu {usage = "xmake sdk-all [-a ARCH] [-m MODE]", description = "Build the kernel, run its tests and export the Kernel SDK", options = common_options}
    on_run(function ()
        import("core.base.option")
        local lane = lane_for(option.get("arch"))
        configure_kernel(option, lane, option.get("mode"))
        run_in(component_dir("kernel"), {"-y", "-b", "okernel"})
        run_in(component_dir("kernel"), {"test"})
        run_in(component_dir("kernel"), {"-y", "-b", "kernel-sdk"})
    end)
task_end()

task("distro-all")
    set_menu {usage = "xmake distro-all [-a ARCH] [-m MODE]", description = "Build the OS consumer against the exported SDK and boot it in QEMU", options = common_options}
    on_run(function ()
        import("core.base.option")
        local lane = lane_for(option.get("arch"))
        configure_os(option, lane, option.get("mode"))
        for _, t in ipairs({"kernel-sdk-check", "uapi-test", "libc-test", "distro_image", "rootfs-ext4"}) do
            run_in(component_dir("os"), {"-y", "-b", t})
        end
        run_in(component_dir("os"), {"qemu-distro", "--fs=ext4", "--require-native", "--timeout=30"})
    end)
task_end()

task("matrix")
    set_menu {usage = "xmake matrix [-m MODE]", description = "Three-architecture fast lane (x86_64, arm32, ppc) across kernel and OS", options = common_options}
    on_run(function ()
        import("core.base.option")
        local failed = {}
        for _, lane in ipairs(fast_lane) do
            local ok = try { function ()
                configure_kernel(option, lane, option.get("mode"))
                run_in(component_dir("kernel"), {"-y", "-b", "okernel"})
                run_in(component_dir("kernel"), {"test"})
                run_in(component_dir("kernel"), {"-y", "-b", "kernel-sdk"})
                configure_os(option, lane, option.get("mode"))
                run_in(component_dir("os"), {"-y", "-b", "kernel-sdk-check"})
                run_in(component_dir("os"), {"-y", "-b", "distro_image"})
                return true
            end }
            if not ok then table.insert(failed, lane.arch) end
        end
        if #failed > 0 then raise("fast lane failed for: %s", table.concat(failed, ", ")) end
        print("fast lane passed: x86_64, arm32, ppc")
    end)
task_end()

task("wt-pair")
    set_menu {usage = "xmake wt-pair --topic=NAME [--kind=feat] [--base=BRANCH]", description = "Create a paired kernel/OS worktree under wt/",
        options = {
            {nil, "topic", "kv", nil, "Topic name, e.g. mm-general"},
            {nil, "kind", "kv", "feat", "Branch prefix: feat, refactor, chore, fix, docs"},
            {nil, "base", "kv", "main", "Base branch in both components"},
            {nil, "kernel-only", "k", nil, "Only the kernel worktree"},
            {nil, "os-only", "k", nil, "Only the OS worktree"},
        }}
    on_run(function ()
        import("core.base.option")
        assert(option.get("topic"), "--topic is required")
        local argv = {path.join(os.projectdir(), "scripts", "wt_pair.py"), "--topic", option.get("topic"),
                      "--kind", option.get("kind"), "--base-branch", option.get("base")}
        if option.get("kernel-only") then table.insert(argv, "--kernel-only") end
        if option.get("os-only") then table.insert(argv, "--os-only") end
        os.execv("python3", argv)
    end)
task_end()

task("sync")
    set_menu {usage = "xmake sync [--pin] [--status]", description = "Synchronise components with manifest.json",
        options = {{nil, "pin", "k", nil, "Rewrite manifest.json from current HEADs"}, {nil, "status", "k", nil, "Compare pinned and current commits"}}}
    on_run(function ()
        import("core.base.option")
        local argv = {path.join(os.projectdir(), "scripts", "sync.py")}
        if option.get("pin") then table.insert(argv, "--pin") end
        if option.get("status") then table.insert(argv, "--status") end
        os.execv("python3", argv)
    end)
task_end()
