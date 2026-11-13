@testset "Configuration" begin

    # parse_port_file
    @testset "parse_port_file" begin

        @testset "single entry" begin
            mktempdir() do dir
                path = joinpath(dir, "test.port")
                write(path, "{'e1': 1}")
                result = Concore.parse_port_file(path)
                @test result == Dict("e1" => 1)
            end
        end

        @testset "multiple entries" begin
            mktempdir() do dir
                path = joinpath(dir, "test.port")
                write(path, "{'e1': 1, 'e2': 2, 'e3': 3}")
                result = Concore.parse_port_file(path)
                @test result == Dict("e1" => 1, "e2" => 2, "e3" => 3)
            end
        end

        @testset "missing file returns empty dict" begin
            result = Concore.parse_port_file("/nonexistent/path/file.port")
            @test result == Dict{String,Int}()
            @test isempty(result)
        end

        @testset "empty file returns empty dict" begin
            mktempdir() do dir
                path = joinpath(dir, "test.port")
                write(path, "")
                result = Concore.parse_port_file(path)
                @test result == Dict{String,Int}()
            end
        end

        @testset "whitespace-only file returns empty dict" begin
            mktempdir() do dir
                path = joinpath(dir, "test.port")
                write(path, "   \n  ")
                result = Concore.parse_port_file(path)
                @test result == Dict{String,Int}()
            end
        end

        @testset "single port with name containing underscore" begin
            mktempdir() do dir
                path = joinpath(dir, "test.port")
                write(path, "{'my_edge': 5}")
                result = Concore.parse_port_file(path)
                @test result == Dict("my_edge" => 5)
            end
        end

        @testset "port with negative value" begin
            mktempdir() do dir
                path = joinpath(dir, "test.port")
                write(path, "{'e1': -1}")
                result = Concore.parse_port_file(path)
                @test result == Dict("e1" => -1)
            end
        end

        @testset "content without braces matches nothing" begin
            mktempdir() do dir
                path = joinpath(dir, "test.port")
                write(path, "random text here")
                result = Concore.parse_port_file(path)
                @test result == Dict{String,Int}()
            end
        end

        @testset "return type is Dict{String,Int}" begin
            mktempdir() do dir
                path = joinpath(dir, "test.port")
                write(path, "{'e1': 1}")
                result = Concore.parse_port_file(path)
                @test result isa Dict{String,Int}
            end
        end

        @testset "port numbers with spaces" begin
            mktempdir() do dir
                path = joinpath(dir, "test.port")
                write(path, "{'e1' : 1 , 'e2' : 2}")
                result = Concore.parse_port_file(path)
                @test result == Dict("e1" => 1, "e2" => 2)
            end
        end

    end

    # load_iport / load_oport
    @testset "load_iport" begin

        @testset "loads from concore.iport file" begin
            mktempdir() do dir
                cd(dir) do
                    write("concore.iport", "{'sensor': 1, 'command': 2}")
                    Concore.iport = Dict{String,Int}()
                    result = Concore.load_iport()
                    @test result == Dict("sensor" => 1, "command" => 2)
                    @test Concore.iport == Dict("sensor" => 1, "command" => 2)
                end
            end
        end

        @testset "returns empty dict when file missing" begin
            mktempdir() do dir
                cd(dir) do
                    Concore.iport = Dict{String,Int}()
                    result = Concore.load_iport()
                    @test isempty(result)
                end
            end
        end

    end

    @testset "load_oport" begin

        @testset "loads from concore.oport file" begin
            mktempdir() do dir
                cd(dir) do
                    write("concore.oport", "{'output': 1}")
                    Concore.oport = Dict{String,Int}()
                    result = Concore.load_oport()
                    @test result == Dict("output" => 1)
                    @test Concore.oport == Dict("output" => 1)
                end
            end
        end

    end

    # load_params
    @testset "load_params" begin

        @testset "Python dict format" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "concore.params"),
                      "{'gain': 2.5, 'mode': 'pid'}")
                Concore.params = Dict{String,Any}()
                Concore.load_params()
                @test Concore.params["gain"] == 2.5
                @test Concore.params["mode"] == "pid"
                Concore.inpath = old_inpath
            end
        end

        @testset "key=value format" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "concore.params"),
                      "gain=2.5;mode=pid")
                Concore.params = Dict{String,Any}()
                Concore.load_params()
                @test Concore.params["gain"] == 2.5
                @test Concore.params["mode"] == "pid"
                Concore.inpath = old_inpath
            end
        end

        @testset "key=value with spaces" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "concore.params"),
                      "gain = 3.0 ; mode = adaptive")
                Concore.params = Dict{String,Any}()
                Concore.load_params()
                @test Concore.params["gain"] == 3.0
                @test Concore.params["mode"] == "adaptive"
                Concore.inpath = old_inpath
            end
        end

        @testset "Windows quoted params" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "concore.params"),
                      "\"{'gain': 1.0}\"")
                Concore.params = Dict{String,Any}()
                Concore.load_params()
                @test Concore.params["gain"] == 1.0
                Concore.inpath = old_inpath
            end
        end

        @testset "missing params file does nothing" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                Concore.params = Dict{String,Any}("existing" => 1.0)
                Concore.load_params()
                @test Concore.params == Dict{String,Any}("existing" => 1.0)
                Concore.inpath = old_inpath
            end
        end

        @testset "empty params file does nothing" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "concore.params"), "")
                Concore.params = Dict{String,Any}("existing" => 1.0)
                Concore.load_params()
                @test Concore.params == Dict{String,Any}("existing" => 1.0)
                Concore.inpath = old_inpath
            end
        end

        @testset "numeric values are Float64" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "concore.params"),
                      "{'x': 42}")
                Concore.params = Dict{String,Any}()
                Concore.load_params()
                @test Concore.params["x"] isa Float64
                @test Concore.params["x"] == 42.0
                Concore.inpath = old_inpath
            end
        end

        @testset "string values are strings" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "concore.params"),
                      "{'mode': 'auto'}")
                Concore.params = Dict{String,Any}()
                Concore.load_params()
                @test Concore.params["mode"] isa AbstractString
                Concore.inpath = old_inpath
            end
        end

    end

    # tryparam
    @testset "tryparam" begin

        @testset "returns value when key exists" begin
            Concore.params = Dict{String,Any}("gain" => 2.5)
            @test Concore.tryparam("gain", 0.0) == 2.5
        end

        @testset "returns default when key missing" begin
            Concore.params = Dict{String,Any}()
            @test Concore.tryparam("missing_key", 99.0) == 99.0
        end

        @testset "returns default of correct type" begin
            Concore.params = Dict{String,Any}()
            @test Concore.tryparam("x", "fallback") == "fallback"
        end

        @testset "works with string values" begin
            Concore.params = Dict{String,Any}("mode" => "pid")
            @test Concore.tryparam("mode", "none") == "pid"
        end

        @testset "does not modify params" begin
            Concore.params = Dict{String,Any}("a" => 1.0)
            Concore.tryparam("b", 2.0)
            @test !haskey(Concore.params, "b")
        end

    end

    # default_maxtime
    @testset "default_maxtime" begin

        @testset "reads from file" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "concore.maxtime"), "500")
                result = Concore.default_maxtime(100)
                @test result == 500
                @test Concore.maxtime == 500
                Concore.inpath = old_inpath
            end
        end

        @testset "uses default when file missing" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                result = Concore.default_maxtime(200)
                @test result == 200
                @test Concore.maxtime == 200
                Concore.inpath = old_inpath
            end
        end

        @testset "uses default when file has bad content" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "concore.maxtime"), "not_a_number")
                result = Concore.default_maxtime(300)
                @test result == 300
                @test Concore.maxtime == 300
                Concore.inpath = old_inpath
            end
        end

        @testset "handles whitespace in file" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "concore.maxtime"), "  750  \n")
                result = Concore.default_maxtime(100)
                @test result == 750
                Concore.inpath = old_inpath
            end
        end

        @testset "sets module global" begin
            mktempdir() do dir
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                Concore.default_maxtime(42)
                @test Concore.maxtime == 42
                Concore.inpath = old_inpath
            end
        end

    end

end
