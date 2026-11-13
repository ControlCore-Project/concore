# File-backend round trips against Python and C++ bindings.
@testset "Cross-language interop" begin

    repo_root = normpath(joinpath(@__DIR__, "..", ".."))
    repo_include = replace(repo_root, "\\" => "/")
    python_path(path) = replace(path, "\\" => "/")

    function reset_interop_state!()
        Concore.simtime = 0.0
        Concore.delay = 0.0
        Concore.s = ""
        Concore.olds = ""
        Concore.retrycount = 0
    end

    function run_cmd(cmd; dir=repo_root)
        try
            return 0, strip(read(Cmd(cmd; dir=dir), String)), ""
        catch err
            return 1, "", sprint(showerror, err)
        end
    end

    @testset "Python writes, Julia reads" begin
        python = Sys.which("python")
        python === nothing && (python = Sys.which("python3"))

        if python === nothing
            @test_skip "python executable not found"
        else
            mktempdir() do dir
                mkpath(joinpath(dir, "out1"))

                script = """
import sys
sys.path.insert(0, "$(python_path(repo_root))")
import concore
concore.delay = 0
concore.simtime = 5.0
concore.outpath = "$(python_path(joinpath(dir, "out")))"
concore.write(1, "signal", [42.0, 3.0])
"""

                code, _out, err = run_cmd(`$python -c $script`)
                @test code == 0
                err != "" && @info err

                old_inpath = Concore.inpath
                try
                    reset_interop_state!()
                    Concore.inpath = joinpath(dir, "out")
                    result = Concore.concore_read(1, "signal", "[0.0, 0.0, 0.0]")

                    @test result == [42.0, 3.0]
                    @test Concore.simtime == 5.0
                    @test read(joinpath(dir, "out1", "signal"), String) == "[5.0, 42.0, 3.0]"
                finally
                    Concore.inpath = old_inpath
                    reset_interop_state!()
                end
            end
        end
    end

    @testset "Julia writes, Python reads" begin
        python = Sys.which("python")
        python === nothing && (python = Sys.which("python3"))

        if python === nothing
            @test_skip "python executable not found"
        else
            mktempdir() do dir
                old_outpath = Concore.outpath
                try
                    reset_interop_state!()
                    Concore.outpath = joinpath(dir, "out")
                    Concore.simtime = 7.0
                    Concore.concore_write(1, "signal", [11.0, 12.5])

                    script = """
import sys
sys.path.insert(0, "$(python_path(repo_root))")
import concore
concore.delay = 0
concore.simtime = 0.0
concore.inpath = "$(python_path(joinpath(dir, "out")))"
value = concore.read(1, "signal", "[0.0, 0.0, 0.0]")
assert value == [11.0, 12.5], value
assert concore.simtime == 7.0, concore.simtime
"""

                    code, _out, err = run_cmd(`$python -c $script`)
                    @test code == 0
                    err != "" && @info err
                finally
                    Concore.outpath = old_outpath
                    reset_interop_state!()
                end
            end
        end
    end

    function cxx_compiler()
        Sys.iswindows() && return nothing

        for name in ("g++", "clang++")
            compiler = Sys.which(name)
            compiler !== nothing && return compiler
        end
        return nothing
    end

    @testset "C++ writes, Julia reads" begin
        compiler = cxx_compiler()

        if compiler === nothing
            @test_skip "C++ compiler not found"
        else
            mktempdir() do dir
                source = joinpath(dir, "write_signal.cpp")
                exe = joinpath(dir, Sys.iswindows() ? "write_signal.exe" : "write_signal")
                write(source, """
#include <vector>
#include "$repo_include/concore.hpp"

int main() {
    Concore c;
    c.delay = 0;
    c.simtime = 9.0;
    c.write_FM(1, "signal", std::vector<double>{13.0, 14.0});
    return 0;
}
""")
                mkpath(joinpath(dir, "out1"))

                code, _out, err = run_cmd(`$compiler -std=c++11 -I$repo_root -o $exe $source`; dir=dir)
                @test code == 0
                err != "" && @info err

                code, _out, err = run_cmd(`$exe`; dir=dir)
                @test code == 0
                err != "" && @info err

                old_inpath = Concore.inpath
                try
                    reset_interop_state!()
                    Concore.inpath = joinpath(dir, "out")
                    result = Concore.concore_read(1, "signal", "[0.0, 0.0, 0.0]")

                    @test result == [13.0, 14.0]
                    @test Concore.simtime == 9.0
                finally
                    Concore.inpath = old_inpath
                    reset_interop_state!()
                end
            end
        end
    end

    @testset "Julia writes, C++ reads" begin
        compiler = cxx_compiler()

        if compiler === nothing
            @test_skip "C++ compiler not found"
        else
            mktempdir() do dir
                old_outpath = Concore.outpath
                try
                    reset_interop_state!()
                    Concore.outpath = joinpath(dir, "out")
                    Concore.simtime = 10.0
                    Concore.concore_write(1, "signal", [21.0, 22.0])
                    mkpath(joinpath(dir, "in1"))
                    cp(joinpath(dir, "out1", "signal"), joinpath(dir, "in1", "signal"))
                finally
                    Concore.outpath = old_outpath
                end

                source = joinpath(dir, "read_signal.cpp")
                exe = joinpath(dir, Sys.iswindows() ? "read_signal.exe" : "read_signal")
                write(source, """
#include <cmath>
#include <vector>
#include "$repo_include/concore.hpp"

int main() {
    Concore c;
    c.delay = 0;
    c.simtime = 0.0;
    std::vector<double> value = c.read_FM(1, "signal", "[0.0, 0.0, 0.0]");
    if (value.size() != 2) return 1;
    if (std::fabs(value[0] - 21.0) > 1e-9) return 2;
    if (std::fabs(value[1] - 22.0) > 1e-9) return 3;
    if (std::fabs(c.simtime - 10.0) > 1e-9) return 4;
    return 0;
}
""")

                code, _out, err = run_cmd(`$compiler -std=c++11 -I$repo_root -o $exe $source`; dir=dir)
                @test code == 0
                err != "" && @info err

                code, _out, err = run_cmd(`$exe`; dir=dir)
                @test code == 0
                err != "" && @info err

                reset_interop_state!()
            end
        end
    end

end
