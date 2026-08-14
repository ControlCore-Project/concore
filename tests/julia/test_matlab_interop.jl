using Test

include(joinpath(@__DIR__, "..", "..", "concore.jl"))
using .Concore

interop_dir = get(ENV, "CONCORE_INTEROP_DIR", "")
if isempty(interop_dir)
    error("CONCORE_INTEROP_DIR is not set")
end

Concore.delay = 0.0

if ARGS[1] == "write"
    rm(interop_dir; recursive=true, force=true)
    Concore.outpath = joinpath(interop_dir, "julia_out")
    Concore.simtime = 12.0
    Concore.concore_write(1, "signal", [21.0, 22.5])

    @test read(joinpath(interop_dir, "julia_out1", "signal"), String) ==
          "[12.0, 21.0, 22.5]"
elseif ARGS[1] == "read"
    Concore.inpath = joinpath(interop_dir, "matlab_out")
    result = Concore.concore_read(1, "signal", "[0.0, 0.0, 0.0]")

    @test result == [31.0, 32.5]
    @test Concore.simtime == 14.0
else
    error("expected write or read")
end
