@testset "ZMQ backend" begin

    function reset_zmq_state!()
        Concore.terminate_zmq()
        Concore._backend = Concore.FileBackend()
        Concore.simtime = 0.0
        Concore.delay = 0.0
        Concore.s = ""
        Concore.olds = ""
        Concore.retrycount = 0
    end

    @testset "backend type" begin
        @test Concore.ZmqBackend <: Concore.AbstractBackend
        @test Concore.ZmqBackend() isa Concore.AbstractBackend
        @test Concore.ZmqTransport === Concore.ZmqBackend
        @test Concore._backend_inpath(Concore.ZmqBackend()) == "zmq://in"
        @test Concore._backend_outpath(Concore.ZmqBackend()) == "zmq://out"
    end

    @testset "soft dependency" begin
        @test Concore.HAS_ZMQ isa Bool
        if Concore.HAS_ZMQ
            @test Concore._require_zmq() === nothing
        else
            @test_throws ErrorException Concore._require_zmq()
            @test_throws ErrorException Concore.init_zmq_port(
                "x", "bind", "tcp://127.0.0.1:5555", "REQ"
            )
        end
    end

    @testset "port registry cleanup" begin
        reset_zmq_state!()
        @test isempty(Concore.zmq_ports)
        @test Concore.terminate_zmq() === nothing
        @test isempty(Concore.zmq_ports)
    end

    @testset "payload format" begin
        reset_zmq_state!()
        Concore.simtime = 5.0
        @test Concore._zmq_payload([42.0, 3.14], 0) == "[5.0, 42.0, 3.14]"
        @test Concore._zmq_payload([1, 2], 1) == "[6.0, 1.0, 2.0]"
        @test Concore._zmq_payload("[7.0, 8.0]", 0) == "[7.0, 8.0]"
    end

    @testset "string port fallback" begin
        mktempdir() do dir
            reset_zmq_state!()
            old_inpath = Concore.inpath
            old_outpath = Concore.outpath
            try
                Concore.inpath = joinpath(dir, "io")
                Concore.outpath = joinpath(dir, "io")
                Concore.simtime = 2.0

                Concore.concore_write("1", "signal", [9.0])
                result = Concore.concore_read("1", "signal", "[0.0, 0.0]")

                @test result == [9.0]
                @test Concore.simtime == 2.0
            finally
                Concore.inpath = old_inpath
                Concore.outpath = old_outpath
                reset_zmq_state!()
            end
        end
    end

    @testset "unregistered string port" begin
        reset_zmq_state!()
        @test_throws ErrorException Concore.concore_read("missing", "signal", "[0.0]")
        @test_throws ErrorException Concore.concore_write("missing", "signal", [1.0])
    end

    if Concore.HAS_ZMQ
        @testset "live REQ to REP send" begin
            using Sockets

            reset_zmq_state!()
            server = Sockets.listen(Sockets.localhost, 0)
            tcp_port = Sockets.getsockname(server)[2]
            close(server)
            address = "tcp://127.0.0.1:$tcp_port"

            Concore.init_zmq_port("rep", "bind", address, "REP")
            Concore.init_zmq_port("req", "connect", address, "REQ")
            @test Concore.zmq_ports["rep"].context === Concore.zmq_ports["req"].context
            sleep(0.1)

            Concore.simtime = 4.0
            Concore.concore_write("req", "signal", [10.0, 11.0])
            result = Concore.concore_read("rep", "signal", "[0.0, 0.0, 0.0]")

            @test result == [10.0, 11.0]
            @test Concore.simtime == 4.0
            reset_zmq_state!()
        end
    else
        @testset "live ZMQ skipped" begin
            @test_skip "ZMQ.jl not installed"
        end
    end

    reset_zmq_state!()

end
