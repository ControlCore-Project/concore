@testset "Mmap backend" begin

    function reset_mmap_state!()
        Concore.mmap_cleanup()
        Concore._backend = Concore.FileBackend()
        Concore.simtime = 0.0
        Concore.delay = 0.0
        Concore.s = ""
        Concore.olds = ""
        Concore.retrycount = 0
    end

    function with_mmap_tempdir(f)
        dir = mktempdir(; cleanup=false)
        try
            f(dir)
        finally
            Concore.mmap_cleanup()
            GC.gc()
            rm(dir; recursive=true, force=true)
        end
    end

    @testset "backend type" begin
        @test Concore.MmapBackend <: Concore.AbstractBackend
        @test Concore.MmapBackend().segment_size == 4096
        @test Concore.MmapBackend(512).segment_size == 512
        @test Concore.MmapTransport === Concore.MmapBackend
        @test_throws ArgumentError Concore.MmapBackend(1)
    end

    @testset "opt in at init" begin
        old_backend = Concore._backend
        try
            Concore.concore_init!(Concore.MmapBackend(512))
            @test Concore._backend isa Concore.MmapBackend
            @test Concore._backend.segment_size == 512
        finally
            Concore._backend = old_backend
            Concore.mmap_cleanup()
        end
    end

    @testset "write uses existing wire format" begin
        with_mmap_tempdir() do dir
            reset_mmap_state!()
            old_outpath = Concore.outpath
            try
                Concore._backend = Concore.MmapBackend(512)
                Concore.outpath = joinpath(dir, "out")
                Concore.simtime = 5.0

                Concore.concore_write(1, "signal", [42.0, 3.14])

                filepath = joinpath(Concore.outpath * "1", "signal")
                @test isfile(filepath)
                @test Concore._mmap_content(Concore._mmap_segments[filepath][2]) == "[5.0, 42.0, 3.14]"
            finally
                Concore.outpath = old_outpath
                reset_mmap_state!()
            end
        end
    end

    @testset "reads normal file backend output" begin
        with_mmap_tempdir() do dir
            reset_mmap_state!()
            old_inpath = Concore.inpath
            try
                Concore._backend = Concore.MmapBackend(512)
                Concore.inpath = joinpath(dir, "in")
                mkpath(Concore.inpath * "1")
                write(joinpath(Concore.inpath * "1", "signal"), "[7.0, 11.0, 12.5]")

                result = Concore.concore_read(1, "signal", "[0.0, 0.0, 0.0]")

                @test result == [11.0, 12.5]
                @test Concore.simtime == 7.0
            finally
                Concore.inpath = old_inpath
                reset_mmap_state!()
            end
        end
    end

    @testset "mmap round trip matches file backend behavior" begin
        with_mmap_tempdir() do dir
            reset_mmap_state!()
            old_inpath = Concore.inpath
            old_outpath = Concore.outpath
            try
                Concore._backend = Concore.MmapBackend(512)
                Concore.inpath = joinpath(dir, "io")
                Concore.outpath = joinpath(dir, "io")
                Concore.simtime = 9.0

                Concore.concore_write(1, "roundtrip", [1.5, 2.5, 3.5])

                Concore.s = ""
                Concore.olds = ""
                Concore.simtime = 0.0
                result = Concore.concore_read(1, "roundtrip", "[0.0, 0.0, 0.0, 0.0]")

                @test result == [1.5, 2.5, 3.5]
                @test Concore.simtime == 9.0
            finally
                Concore.inpath = old_inpath
                Concore.outpath = old_outpath
                reset_mmap_state!()
            end
        end
    end

    @testset "file backend reads mmap output" begin
        with_mmap_tempdir() do dir
            reset_mmap_state!()
            old_inpath = Concore.inpath
            old_outpath = Concore.outpath
            try
                Concore.inpath = joinpath(dir, "io")
                Concore.outpath = joinpath(dir, "io")
                Concore._backend = Concore.MmapBackend(512)
                Concore.simtime = 4.0

                Concore.concore_write(1, "signal", [8.0, 9.0])

                Concore._backend = Concore.FileBackend()
                Concore.simtime = 0.0
                result = Concore.concore_read(1, "signal", "[0.0, 0.0, 0.0]")

                @test result == [8.0, 9.0]
                @test Concore.simtime == 4.0
            finally
                Concore.inpath = old_inpath
                Concore.outpath = old_outpath
                reset_mmap_state!()
            end
        end
    end

    @testset "file backend can overwrite mapped path" begin
        with_mmap_tempdir() do dir
            reset_mmap_state!()
            old_inpath = Concore.inpath
            old_outpath = Concore.outpath
            try
                Concore.inpath = joinpath(dir, "io")
                Concore.outpath = joinpath(dir, "io")
                Concore._backend = Concore.MmapBackend(512)
                Concore.concore_write(1, "signal", [1.0])

                Concore._backend = Concore.FileBackend()
                Concore.simtime = 2.0
                Concore.concore_write(1, "signal", [20.0])
                result = Concore.concore_read(1, "signal", "[0.0, 0.0]")

                @test result == [20.0]
                @test Concore.simtime == 2.0
            finally
                Concore.inpath = old_inpath
                Concore.outpath = old_outpath
                reset_mmap_state!()
            end
        end
    end

    @testset "shorter writes clear stale bytes" begin
        with_mmap_tempdir() do dir
            reset_mmap_state!()
            old_outpath = Concore.outpath
            try
                Concore._backend = Concore.MmapBackend(512)
                Concore.outpath = joinpath(dir, "out")

                Concore.concore_write(1, "signal", [100.0, 200.0, 300.0])
                Concore.concore_write(1, "signal", [1.0])

                filepath = joinpath(Concore.outpath * "1", "signal")
                @test Concore._mmap_content(Concore._mmap_segments[filepath][2]) == "[0.0, 1.0]"
            finally
                Concore.outpath = old_outpath
                reset_mmap_state!()
            end
        end
    end

    @testset "payload must fit segment" begin
        with_mmap_tempdir() do dir
            reset_mmap_state!()
            old_outpath = Concore.outpath
            try
                Concore._backend = Concore.MmapBackend(16)
                Concore.outpath = joinpath(dir, "out")

                @test_throws ArgumentError Concore.concore_write(1, "signal", [1.0, 2.0, 3.0])
            finally
                Concore.outpath = old_outpath
                reset_mmap_state!()
            end
        end
    end

end
