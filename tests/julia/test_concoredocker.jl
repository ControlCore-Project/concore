module DockerRuntime
include(joinpath(@__DIR__, "..", "..", "concoredocker.jl"))
end

const DockerConcore = DockerRuntime.Concore

@testset "Concore Docker runtime" begin

    function reset_docker_state!()
        DockerConcore._backend = DockerConcore.FileBackend()
        DockerConcore.inpath = "/in"
        DockerConcore.outpath = "/out"
        DockerConcore.simtime = 0.0
        DockerConcore.delay = 0.0
        DockerConcore.s = ""
        DockerConcore.olds = ""
        DockerConcore.retrycount = 0
        DockerConcore.params = Dict{String,Any}()
    end

    @testset "default paths" begin
        reset_docker_state!()
        @test DockerConcore.inpath == "/in"
        @test DockerConcore.outpath == "/out"
        @test DockerConcore._backend_inpath(DockerConcore.FileBackend()) == "/in"
        @test DockerConcore._backend_outpath(DockerConcore.FileBackend()) == "/out"
        @test DockerConcore._input_dir(1) == "/in1"
        @test DockerConcore._output_dir(2) == "/out2"
    end

    @testset "basic API" begin
        reset_docker_state!()
        @test DockerConcore.initval("[3.0, 10.0, 20.0]") == [10.0, 20.0]
        @test DockerConcore.simtime == 3.0

        DockerConcore.params = Dict{String,Any}("gain" => 2.5)
        @test DockerConcore.tryparam("gain", 1.0) == 2.5
        @test DockerConcore.tryparam("missing", 7.0) == 7.0
    end

    @testset "read and write" begin
        mktempdir() do dir
            reset_docker_state!()
            DockerConcore.inpath = joinpath(dir, "in")
            DockerConcore.outpath = joinpath(dir, "out")
            DockerConcore.simtime = 5.0

            DockerConcore.concore_write(1, "signal", [42.0])
            path = joinpath(DockerConcore.outpath * "1", "signal")
            @test read(path, String) == "[5.0, 42.0]"

            DockerConcore.inpath = DockerConcore.outpath
            DockerConcore.simtime = 0.0
            @test DockerConcore.concore_read(1, "signal", "[0.0, 0.0]") == [42.0]
            @test DockerConcore.simtime == 5.0
        end
    end

    @testset "aliases" begin
        mktempdir() do dir
            reset_docker_state!()
            DockerConcore.inpath = joinpath(dir, "io")
            DockerConcore.outpath = joinpath(dir, "io")
            DockerConcore.simtime = 9.0

            DockerConcore.write(1, "alias_signal", [1.5, 2.5])
            DockerConcore.simtime = 0.0
            @test DockerConcore.read(1, "alias_signal", "[0.0, 0.0, 0.0]") == [1.5, 2.5]
            @test DockerConcore.simtime == 9.0
        end
    end

    @testset "maxtime" begin
        mktempdir() do dir
            reset_docker_state!()
            DockerConcore.inpath = joinpath(dir, "in")
            mkpath(DockerConcore.inpath * "1")
            write(joinpath(DockerConcore.inpath * "1", "concore.maxtime"), "75")

            @test DockerConcore.default_maxtime(100) == 75
            @test DockerConcore.maxtime == 75
        end
    end

end