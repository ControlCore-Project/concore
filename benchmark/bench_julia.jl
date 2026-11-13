include(joinpath(@__DIR__, "..", "concore.jl"))
using .Concore
using Printf
using Sockets
using Statistics

const QUICK = "--quick" in ARGS
const ITERATIONS = QUICK ? 100 : 5_000
const WARMUP = QUICK ? 10 : 100
const REPEATS = QUICK ? 3 : 5
const PAYLOAD = [1.0, 2.0, 3.0, 4.0]
const WIRE = "[0.0, 1.0, 2.0, 3.0, 4.0]"
const INITIAL = "[0.0, 0.0, 0.0, 0.0, 0.0]"

function measure(label, unit, f, expected)
    result = nothing
    for _ in 1:WARMUP
        result = f()
    end
    result == expected || error("$label warmup returned an unexpected value")

    elapsed = Vector{Float64}(undef, REPEATS)
    for repeat in 1:REPEATS
        start = time_ns()
        for _ in 1:ITERATIONS
            result = f()
        end
        elapsed[repeat] = (time_ns() - start) / 1e9
        result == expected || error("$label returned an unexpected value")
    end

    seconds = median(elapsed)
    rate = ITERATIONS / seconds
    @printf("%-24s %12.3f %18.0f %s/s\n", label, seconds * 1e3, rate, unit)
end

function reset_state!()
    Concore.simtime = 0.0
    Concore.delay = 0.0
    Concore.s = ""
    Concore.olds = ""
    Concore.retrycount = 0
end

function file_roundtrip()
    Concore.concore_write(1, "request", PAYLOAD)
    request = Concore.concore_read(1, "request", INITIAL)
    Concore.concore_write(1, "reply", request)
    reply = Concore.concore_read(1, "reply", INITIAL)
    Concore.s = ""
    Concore.olds = ""
    return reply
end

function benchmark_file_backend(label, backend)
    dir = mktempdir(; cleanup=false)
    old_backend = Concore._backend
    old_inpath = Concore.inpath
    old_outpath = Concore.outpath
    old_delay = Concore.delay
    try
        path = joinpath(dir, "io")
        mkpath(path * "1")
        Concore.inpath = path
        Concore.outpath = path
        Concore.concore_init!(backend)
        reset_state!()
        measure(label, "round trips", file_roundtrip, PAYLOAD)
    finally
        Concore.mmap_cleanup()
        Concore._backend = old_backend
        Concore.inpath = old_inpath
        Concore.outpath = old_outpath
        reset_state!()
        Concore.delay = old_delay
        GC.gc()
        rm(dir; recursive=true, force=true)
    end
end

function benchmark_zmq()
    if !Concore.HAS_ZMQ
        println("ZMQ round trip           skipped (ZMQ.jl is not installed)")
        return
    end

    server = Sockets.listen(Sockets.localhost, 0)
    port = Sockets.getsockname(server)[2]
    close(server)
    address = "tcp://127.0.0.1:$port"
    old_backend = Concore._backend
    old_delay = Concore.delay

    try
        Concore.concore_init!(Concore.ZmqBackend())
        reset_state!()
        Concore.init_zmq_port("rep", "bind", address, "REP")
        Concore.init_zmq_port("req", "connect", address, "REQ")
        sleep(0.1)

        function zmq_roundtrip()
            Concore.concore_write("req", "request", PAYLOAD)
            request = Concore.concore_read("rep", "request", INITIAL)
            Concore.concore_write("rep", "reply", request)
            reply = Concore.concore_read("req", "reply", INITIAL)
            return reply
        end

        measure("ZMQ round trip", "round trips", zmq_roundtrip, PAYLOAD)
    finally
        Concore.terminate_zmq()
        Concore._backend = old_backend
        reset_state!()
        Concore.delay = old_delay
    end
end

unexpected = filter(arg -> arg != "--quick", ARGS)
isempty(unexpected) || error("unknown argument: $(first(unexpected))")

println("Julia $(VERSION) | $(Sys.KERNEL) $(Sys.MACHINE)")
println("iterations=$ITERATIONS warmup=$WARMUP repeats=$REPEATS")
println()
@printf("%-24s %12s %18s\n", "workload", "median ms", "rate")
println("-" ^ 58)

measure("Parse wire", "operations", () -> Concore.safe_parse_list(WIRE), [0.0; PAYLOAD])
measure("Format wire", "operations", () -> Concore._format_wire([0.0; PAYLOAD]), WIRE)
benchmark_file_backend("File round trip", Concore.FileBackend())
benchmark_file_backend("Mmap round trip", Concore.MmapBackend())
benchmark_zmq()
