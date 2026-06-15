@testset "Protocol Core" begin

    # Reset state helper
    function reset_concore_state!()
        Concore.simtime = 0.0
        Concore.delay = 0.0  # zero delay for fast tests
        Concore.s = ""
        Concore.olds = ""
        Concore.retrycount = 0
    end

    # concore_write (Vector{Float64})
    @testset "concore_write basics" begin

        @testset "creates file with correct format" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 5.0

                Concore.concore_write(1, "test_signal", [42.0, 3.14])

                filepath = joinpath(Concore.outpath * "1", "test_signal")
                @test isfile(filepath)
                content = read(filepath, String)
                @test content == "[5.0, 42.0, 3.14]"
                Concore.outpath = old_outpath
            end
        end

        @testset "creates output directory" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")

                Concore.concore_write(1, "signal", [1.0])

                @test isdir(Concore.outpath * "1")
                Concore.outpath = old_outpath
            end
        end

        @testset "integer-valued floats keep .0 suffix" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 0.0

                Concore.concore_write(1, "test", [42.0])

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test content == "[0.0, 42.0]"
                @test occursin("42.0", content)
                @test !occursin("42,", content)
                Concore.outpath = old_outpath
            end
        end

        @testset "delta=0 does not advance simtime" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 10.0

                Concore.concore_write(1, "test", [1.0]; delta=0)

                @test Concore.simtime == 10.0
                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test startswith(content, "[10.0")
                Concore.outpath = old_outpath
            end
        end

        @testset "delta=1 writes correct timestamp in wire" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 10.0

                Concore.concore_write(1, "test", [1.0]; delta=1)

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test startswith(content, "[11.0")
                Concore.outpath = old_outpath
            end
        end

        @testset "empty value array writes only simtime" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 3.0

                Concore.concore_write(1, "test", Float64[])

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test content == "[3.0]"
                Concore.outpath = old_outpath
            end
        end

        @testset "multiple values" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 1.0

                Concore.concore_write(1, "test", [10.0, 20.0, 30.0, 40.0, 50.0])

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test content == "[1.0, 10.0, 20.0, 30.0, 40.0, 50.0]"
                Concore.outpath = old_outpath
            end
        end

        @testset "negative values" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 0.0

                Concore.concore_write(1, "test", [-1.5, -2.5])

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test content == "[0.0, -1.5, -2.5]"
                Concore.outpath = old_outpath
            end
        end

        @testset "non-integer floats format correctly" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 0.0

                Concore.concore_write(1, "test", [3.14159])

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test occursin("3.14159", content)
                Concore.outpath = old_outpath
            end
        end

        @testset "different port numbers" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 0.0

                Concore.concore_write(1, "test", [1.0])
                Concore.concore_write(2, "test", [2.0])
                Concore.concore_write(3, "test", [3.0])

                @test isfile(joinpath(Concore.outpath * "1", "test"))
                @test isfile(joinpath(Concore.outpath * "2", "test"))
                @test isfile(joinpath(Concore.outpath * "3", "test"))
                Concore.outpath = old_outpath
            end
        end

        @testset "overwrite existing file" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 0.0

                Concore.concore_write(1, "test", [1.0])
                Concore.concore_write(1, "test", [2.0])

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test content == "[0.0, 2.0]"
                Concore.outpath = old_outpath
            end
        end

    end

    # concore_write (String variant)
    @testset "concore_write string variant" begin

        @testset "writes raw string" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")

                Concore.concore_write(1, "raw_test", "[99.0, 1.0, 2.0]")

                content = read(joinpath(Concore.outpath * "1", "raw_test"), String)
                @test content == "[99.0, 1.0, 2.0]"
                Concore.outpath = old_outpath
            end
        end

        @testset "string write creates directory" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")

                Concore.concore_write(1, "test", "hello")

                @test isdir(Concore.outpath * "1")
                Concore.outpath = old_outpath
            end
        end

        @testset "string write preserves exact content" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")

                raw = "[0.0, np.float64(1.5), True]"
                Concore.concore_write(1, "test", raw)

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test content == raw
                Concore.outpath = old_outpath
            end
        end

    end

    # concore_read
    @testset "concore_read" begin

        @testset "reads data file and extracts values after simtime" begin
            mktempdir() do dir
                reset_concore_state!()
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "signal"), "[5.0, 42.0, 3.14]")

                result = Concore.concore_read(1, "signal", "[0.0, 0.0, 0.0]")

                @test result == [42.0, 3.14]
                @test Concore.simtime == 5.0
                Concore.inpath = old_inpath
            end
        end

        @testset "falls back to initstr when file missing" begin
            mktempdir() do dir
                reset_concore_state!()
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")

                result = Concore.concore_read(1, "nosuchfile", "[0.0, 1.0, 2.0]")

                @test result == [1.0, 2.0]
                @test Concore.simtime == 0.0
                Concore.inpath = old_inpath
            end
        end

        @testset "updates simtime from data" begin
            mktempdir() do dir
                reset_concore_state!()
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "signal"), "[10.0, 1.0]")

                Concore.concore_read(1, "signal", "[0.0, 0.0]")

                @test Concore.simtime == 10.0
                Concore.inpath = old_inpath
            end
        end

        @testset "simtime uses max (doesn't go backwards)" begin
            mktempdir() do dir
                reset_concore_state!()
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")

                Concore.simtime = 20.0
                write(joinpath(Concore.inpath * "1", "signal"), "[5.0, 1.0]")
                Concore.concore_read(1, "signal", "[0.0, 0.0]")

                @test Concore.simtime == 20.0
                Concore.inpath = old_inpath
            end
        end

        @testset "accumulates into s string for sync" begin
            mktempdir() do dir
                reset_concore_state!()
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "signal"), "[0.0, 1.0]")

                @test Concore.s == ""
                Concore.concore_read(1, "signal", "[0.0, 0.0]")
                @test Concore.s != ""
                Concore.inpath = old_inpath
            end
        end

        @testset "read from different ports" begin
            mktempdir() do dir
                reset_concore_state!()
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                mkpath(Concore.inpath * "2")
                write(joinpath(Concore.inpath * "1", "s1"), "[0.0, 10.0]")
                write(joinpath(Concore.inpath * "2", "s2"), "[0.0, 20.0]")

                r1 = Concore.concore_read(1, "s1", "[0.0, 0.0]")
                r2 = Concore.concore_read(2, "s2", "[0.0, 0.0]")

                @test r1 == [10.0]
                @test r2 == [20.0]
                Concore.inpath = old_inpath
            end
        end

        @testset "single value (just simtime + one value)" begin
            mktempdir() do dir
                reset_concore_state!()
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "signal"), "[0.0, 99.0]")

                result = Concore.concore_read(1, "signal", "[0.0, 0.0]")
                @test result == [99.0]
                @test length(result) == 1
                Concore.inpath = old_inpath
            end
        end

        @testset "multiple values" begin
            mktempdir() do dir
                reset_concore_state!()
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "signal"), "[0.0, 1.0, 2.0, 3.0, 4.0, 5.0]")

                result = Concore.concore_read(1, "signal", "[0.0, 0.0]")
                @test result == [1.0, 2.0, 3.0, 4.0, 5.0]
                @test length(result) == 5
                Concore.inpath = old_inpath
            end
        end

    end

    # Write then Read round-trip
    @testset "write-read round-trip" begin

        @testset "data survives round-trip" begin
            mktempdir() do dir
                reset_concore_state!()
                old_inpath = Concore.inpath
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "io")
                Concore.inpath = joinpath(dir, "io")
                Concore.simtime = 5.0

                original = [42.0, 3.14, -1.5]
                Concore.concore_write(1, "roundtrip", original)

                reset_concore_state!()
                Concore.inpath = joinpath(dir, "io")
                result = Concore.concore_read(1, "roundtrip", "[0.0, 0.0, 0.0, 0.0]")

                @test result ≈ original
                @test Concore.simtime == 5.0

                Concore.inpath = old_inpath
                Concore.outpath = old_outpath
            end
        end

        @testset "integer values round-trip correctly" begin
            mktempdir() do dir
                reset_concore_state!()
                old_inpath = Concore.inpath
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "io")
                Concore.inpath = joinpath(dir, "io")
                Concore.simtime = 0.0

                original = [1.0, 2.0, 3.0]
                Concore.concore_write(1, "roundtrip", original)

                reset_concore_state!()
                Concore.inpath = joinpath(dir, "io")
                result = Concore.concore_read(1, "roundtrip", "[0.0, 0.0, 0.0, 0.0]")

                @test result == original

                Concore.inpath = old_inpath
                Concore.outpath = old_outpath
            end
        end

        @testset "simtime preserved in round-trip" begin
            mktempdir() do dir
                reset_concore_state!()
                old_inpath = Concore.inpath
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "io")
                Concore.inpath = joinpath(dir, "io")
                Concore.simtime = 99.0

                Concore.concore_write(1, "roundtrip", [1.0])

                reset_concore_state!()
                Concore.inpath = joinpath(dir, "io")
                Concore.concore_read(1, "roundtrip", "[0.0, 0.0]")

                @test Concore.simtime == 99.0

                Concore.inpath = old_inpath
                Concore.outpath = old_outpath
            end
        end

    end

    # Wire format verification
    @testset "wire format" begin

        @testset "output starts with [ and ends with ]" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 0.0

                Concore.concore_write(1, "test", [1.0, 2.0])

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test startswith(content, "[")
                @test endswith(content, "]")
                Concore.outpath = old_outpath
            end
        end

        @testset "values separated by comma-space" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 0.0

                Concore.concore_write(1, "test", [1.0, 2.0, 3.0])

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test content == "[0.0, 1.0, 2.0, 3.0]"
                @test occursin(", ", content)
                Concore.outpath = old_outpath
            end
        end

        @testset "no trailing comma" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 0.0

                Concore.concore_write(1, "test", [1.0])

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test !endswith(content, ",]")
                @test !endswith(content, ", ]")
                Concore.outpath = old_outpath
            end
        end

        @testset "no newline in output" begin
            mktempdir() do dir
                reset_concore_state!()
                old_outpath = Concore.outpath
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 0.0

                Concore.concore_write(1, "test", [1.0, 2.0])

                content = read(joinpath(Concore.outpath * "1", "test"), String)
                @test !occursin('\n', content)
                Concore.outpath = old_outpath
            end
        end

    end

end
