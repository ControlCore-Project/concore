using Test

include(joinpath(@__DIR__, "..", "..", "concore.jl"))
using .Concore

repo_root = normpath(joinpath(@__DIR__, "..", ".."))
iverilog = Sys.which("iverilog")
vvp = Sys.which("vvp")
iverilog === nothing && error("iverilog executable not found")
vvp === nothing && error("vvp executable not found")

@testset "Verilog interop" begin
    mktempdir() do dir
        Concore.delay = 0.0
        Concore.outpath = joinpath(dir, "in")
        Concore.simtime = 12.0
        Concore.concore_write(1, "signal", [21.0, 22.5])
        mkpath(joinpath(dir, "out1"))

        source = joinpath(dir, "julia_interop.v")
        simulation = joinpath(dir, "julia_interop")
        write(source, """
`include "concore.v"

module julia_interop;
reg [8*13-1:0] init_signal = "[0.0,0.0,0.0]";

initial begin
  #1;
  concore.readdata(1, "signal", init_signal);
  if (concore.datasize != 2) \$fatal(1, "unexpected data size");
  if (concore.simtime != 12.0) \$fatal(1, "unexpected simtime");
  if (concore.data[0] != 21.0) \$fatal(1, "unexpected first value");
  if (concore.data[1] != 22.5) \$fatal(1, "unexpected second value");

  concore.simtime = 14.0;
  concore.datasize = 2;
  concore.data[0] = 31.0;
  concore.data[1] = 32.5;
  concore.writedata(1, "signal", 0);
  \$finish;
end
endmodule
""")

        run(Cmd(`$iverilog -g2012 -I$repo_root -o $simulation $source`; dir=dir))
        run(Cmd(`$vvp $simulation`; dir=dir))

        Concore.inpath = joinpath(dir, "out")
        Concore.simtime = 0.0
        result = Concore.concore_read(1, "signal", "[0.0, 0.0, 0.0]")

        @test result == [31.0, 32.5]
        @test Concore.simtime == 14.0
    end
end
