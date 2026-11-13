# run_julia_mixed_demo.jl -- run Python/Julia concore demo pairs
#
# Usage:
#     julia demo/run_julia_mixed_demo.jl [maxtime]

const DEMO_DIR = @__DIR__
const REPO_ROOT = dirname(DEMO_DIR)
const MAXTIME = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 5
const PYTHON = get(ENV, "PYTHON", Sys.iswindows() ? "python" : "python3")

function link_dir(target, link)
    ispath(link) && return
    try
        symlink(target, link; dir_target=true)
    catch
        if Sys.iswindows()
            run(`cmd /c mklink /J $link $target`)
        else
            rethrow()
        end
    end
end

function prepare_node(node_dir, in_edge, out_edge, source_file, runtime_files)
    mkpath(node_dir)
    link_dir(in_edge, joinpath(node_dir, "in1"))
    link_dir(out_edge, joinpath(node_dir, "out1"))
    cp(source_file, joinpath(node_dir, basename(source_file)); force=true)
    for runtime_file in runtime_files
        cp(runtime_file, joinpath(node_dir, basename(runtime_file)); force=true)
    end
end

function wait_with_timeout(procs, timeout_sec)
    start = time()
    while any(process_running, procs)
        if time() - start > timeout_sec
            for proc in procs
                process_running(proc) && kill(proc)
            end
            return false
        end
        sleep(0.1)
    end
    return true
end

function run_pair(label, controller_source, controller_cmd, pm_source, pm_cmd)
    workspace = mktempdir(; cleanup=true)
    cu_dir = joinpath(workspace, "CU")
    pym_dir = joinpath(workspace, "PYM")
    cz_dir = joinpath(workspace, "CZ")
    pz_dir = joinpath(workspace, "PZ")

    mkpath(cu_dir)
    mkpath(pym_dir)

    write(joinpath(cu_dir, "u"), "[0.0, 0.0]")
    write(joinpath(pym_dir, "ym"), "[0.0, 0.0]")
    write(joinpath(cu_dir, "concore.maxtime"), string(MAXTIME))
    write(joinpath(pym_dir, "concore.maxtime"), string(MAXTIME))

    prepare_node(
        cz_dir,
        pym_dir,
        cu_dir,
        controller_source,
        endswith(controller_source, ".jl") ?
            [joinpath(REPO_ROOT, "concore.jl")] :
            [joinpath(REPO_ROOT, "concore.py"), joinpath(REPO_ROOT, "concore_base.py")],
    )
    prepare_node(
        pz_dir,
        cu_dir,
        pym_dir,
        pm_source,
        endswith(pm_source, ".jl") ?
            [joinpath(REPO_ROOT, "concore.jl")] :
            [joinpath(REPO_ROOT, "concore.py"), joinpath(REPO_ROOT, "concore_base.py")],
    )

    write(joinpath(cz_dir, "concore.iport"), "{'ym': 1}")
    write(joinpath(cz_dir, "concore.oport"), "{'u': 1}")
    write(joinpath(pz_dir, "concore.iport"), "{'u': 1}")
    write(joinpath(pz_dir, "concore.oport"), "{'ym': 1}")

    controller_out = joinpath(cz_dir, "concoreout.txt")
    pm_out = joinpath(pz_dir, "concoreout.txt")

    println("Running $label")
    controller_proc = open(controller_out, "w") do out
        run(pipeline(Cmd(controller_cmd; dir=cz_dir), stdout=out, stderr=out); wait=false)
    end
    pm_proc = open(pm_out, "w") do out
        run(pipeline(Cmd(pm_cmd; dir=pz_dir), stdout=out, stderr=out); wait=false)
    end

    completed = wait_with_timeout([controller_proc, pm_proc], 60)
    wait(controller_proc)
    wait(pm_proc)

    controller_log = read(controller_out, String)
    pm_log = read(pm_out, String)
    final_ym = read(joinpath(pym_dir, "ym"), String)

    ok = completed &&
         controller_proc.exitcode == 0 &&
         pm_proc.exitcode == 0 &&
         occursin("retry=", controller_log) &&
         occursin("retry=", pm_log) &&
         startswith(strip(final_ym), "[")

    if ok
        println("PASS: $label")
    else
        println("FAIL: $label")
        println("--- controller output ---")
        print(controller_log)
        println("--- plant output ---")
        print(pm_log)
    end

    return ok
end

julia_cmd = Base.julia_cmd()

ok_controller_jl = run_pair(
    "Julia controller + Python plant",
    joinpath(DEMO_DIR, "controller_jl.jl"),
    `$julia_cmd controller_jl.jl`,
    joinpath(DEMO_DIR, "pm.py"),
    `$PYTHON pm.py`,
)

ok_pm_jl = run_pair(
    "Python controller + Julia plant",
    joinpath(DEMO_DIR, "controller.py"),
    `$PYTHON controller.py`,
    joinpath(DEMO_DIR, "pm_jl.jl"),
    `$julia_cmd pm_jl.jl`,
)

exit(ok_controller_jl && ok_pm_jl ? 0 : 1)
