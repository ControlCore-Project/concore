@testset "Synchronization" begin

    function reset_sync_state!()
        Concore.simtime = 0.0
        Concore.delay = 0.0
        Concore.s = ""
        Concore.olds = ""
        Concore.retrycount = 0
    end

    # initval
    @testset "initval" begin

        @testset "sets simtime from first element" begin
            reset_sync_state!()
            Concore.initval("[5.0, 1.0, 2.0]")
            @test Concore.simtime == 5.0
        end

        @testset "returns data portion without simtime" begin
            reset_sync_state!()
            result = Concore.initval("[5.0, 1.0, 2.0]")
            @test result == [1.0, 2.0]
        end

        @testset "single value after simtime" begin
            reset_sync_state!()
            result = Concore.initval("[0.0, 42.0]")
            @test result == [42.0]
            @test Concore.simtime == 0.0
        end

        @testset "simtime=0" begin
            reset_sync_state!()
            result = Concore.initval("[0.0, 0.0]")
            @test result == [0.0]
            @test Concore.simtime == 0.0
        end

        @testset "large simtime" begin
            reset_sync_state!()
            result = Concore.initval("[999.0, 1.0]")
            @test Concore.simtime == 999.0
            @test result == [1.0]
        end

        @testset "multiple data values" begin
            reset_sync_state!()
            result = Concore.initval("[0.0, 1.0, 2.0, 3.0, 4.0, 5.0]")
            @test result == [1.0, 2.0, 3.0, 4.0, 5.0]
        end

        @testset "return type is Vector{Float64}" begin
            reset_sync_state!()
            result = Concore.initval("[0.0, 1.0]")
            @test result isa Vector{Float64}
        end

        @testset "overwrites previous simtime" begin
            reset_sync_state!()
            Concore.simtime = 100.0
            Concore.initval("[5.0, 1.0]")
            @test Concore.simtime == 5.0
        end

        @testset "handles negative values" begin
            reset_sync_state!()
            result = Concore.initval("[0.0, -1.5, -2.5]")
            @test result == [-1.5, -2.5]
        end

    end

    # unchanged
    @testset "unchanged" begin

        @testset "returns true when no reads happened (s == olds == empty)" begin
            reset_sync_state!()
            @test Concore.unchanged() == true
        end

        @testset "returns false after s is modified (simulating read)" begin
            reset_sync_state!()
            Concore.s = "some data"
            @test Concore.unchanged() == false
        end

        @testset "returns true on second call without new data" begin
            reset_sync_state!()
            Concore.s = "some data"
            Concore.unchanged()  # first call: detects change, returns false
            @test Concore.unchanged() == true  # second call: no new data
        end

        @testset "clears s when returning true" begin
            reset_sync_state!()
            Concore.unchanged()
            @test Concore.s == ""
        end

        @testset "updates olds when returning false" begin
            reset_sync_state!()
            Concore.s = "new data"
            Concore.unchanged()
            @test Concore.olds == "new data"
        end

        @testset "detects new data after reset" begin
            reset_sync_state!()
            Concore.s = "first read"
            @test Concore.unchanged() == false
            @test Concore.unchanged() == true
            Concore.s = "second read"
            @test Concore.unchanged() == false
        end

        @testset "accumulation pattern (read appends to s)" begin
            reset_sync_state!()
            Concore.s *= "[0.0, 1.0]"
            @test Concore.unchanged() == false
            Concore.s *= "[1.0, 2.0]"
            @test Concore.unchanged() == false
        end

    end

    # Sync pattern integration
    @testset "sync pattern with read" begin

        @testset "unchanged detects concore_read activity" begin
            mktempdir() do dir
                reset_sync_state!()
                old_inpath = Concore.inpath
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "signal"), "[0.0, 1.0]")

                @test Concore.unchanged() == true
                Concore.concore_read(1, "signal", "[0.0, 0.0]")
                @test Concore.unchanged() == false
                @test Concore.unchanged() == true

                Concore.inpath = old_inpath
            end
        end

    end

end
