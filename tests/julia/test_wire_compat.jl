# Exact wire strings that must stay readable across Concore runtimes.
@testset "Wire compatibility" begin

    function reset_wire_state!()
        Concore.simtime = 0.0
        Concore.delay = 0.0
        Concore.s = ""
        Concore.olds = ""
        Concore.retrycount = 0
    end

    @testset "Julia writes Python-style wire strings" begin
        cases = [
            (0.0, [0.0], "[0.0, 0.0]"),
            (0.0, [1.0, 2.0, 3.0], "[0.0, 1.0, 2.0, 3.0]"),
            (5.0, [42.0, 3.0], "[5.0, 42.0, 3.0]"),
            (2.0, [3.14, -1.5, 0.0], "[2.0, 3.14, -1.5, 0.0]"),
        ]

        mktempdir() do dir
            old_outpath = Concore.outpath
            Concore.outpath = joinpath(dir, "out")

            try
                for (simtime, values, expected) in cases
                    reset_wire_state!()
                    Concore.simtime = simtime
                    Concore.concore_write(1, "wire", values)
                    content = read(joinpath(dir, "out1", "wire"), String)

                    @test content == expected
                    @test !occursin('\n', content)
                    @test !endswith(content, ",]")
                    @test !endswith(content, ", ]")
                end
            finally
                Concore.outpath = old_outpath
                reset_wire_state!()
            end
        end
    end

    @testset "Julia parses Python and C++ wire strings" begin
        @test Concore.safe_parse_list("[5.0, 42.0, 3.0]") == [5.0, 42.0, 3.0]
        @test Concore.safe_parse_list("[5,42,3]") == [5.0, 42.0, 3.0]
        @test Concore.safe_parse_list("[np.float64(5.0), np.float64(42.0)]") == [5.0, 42.0]
        @test Concore.safe_parse_list("np.array([1.0, 2.0, 3.0])") == [1.0, 2.0, 3.0]
    end

    @testset "delta affects written simtime only" begin
        mktempdir() do dir
            old_outpath = Concore.outpath
            Concore.outpath = joinpath(dir, "out")

            try
                reset_wire_state!()
                Concore.simtime = 5.0
                Concore.concore_write(1, "ym", [3.01]; delta=1)

                content = read(joinpath(dir, "out1", "ym"), String)
                @test content == "[6.0, 3.01]"
                @test Concore.simtime == 5.0
            finally
                Concore.outpath = old_outpath
                reset_wire_state!()
            end
        end
    end

end
