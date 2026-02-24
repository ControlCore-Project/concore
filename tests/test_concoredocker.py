import os
import pytest


class TestSafeLiteralEval:

    def test_reads_dictionary_from_file(self, temp_dir):
        test_file = os.path.join(temp_dir, "ports.txt")
        with open(test_file, "w") as f:
            f.write("{'a': 1, 'b': 2}")

        from concoredocker import safe_literal_eval
        result = safe_literal_eval(test_file, {})

        assert result == {'a': 1, 'b': 2}

    def test_reads_list_from_file(self, temp_dir):
        test_file = os.path.join(temp_dir, "data.txt")
        with open(test_file, "w") as f:
            f.write("[1, 2, 3]")

        from concoredocker import safe_literal_eval
        result = safe_literal_eval(test_file, [])

        assert result == [1, 2, 3]

    def test_returns_default_when_file_missing(self):
        from concoredocker import safe_literal_eval
        result = safe_literal_eval("/nonexistent.txt", {'default': True})

        assert result == {'default': True}

    def test_returns_default_for_bad_syntax(self, temp_dir):
        test_file = os.path.join(temp_dir, "bad.txt")
        with open(test_file, "w") as f:
            f.write("not valid {{{")

        from concoredocker import safe_literal_eval
        result = safe_literal_eval(test_file, "fallback")

        assert result == "fallback"


class TestUnchanged:

    def test_returns_true_when_unchanged(self):
        import concoredocker
        concoredocker.s = "abc"
        concoredocker.olds = "abc"

        assert concoredocker.unchanged() == True
        assert concoredocker.s == ''

    def test_returns_false_when_changed(self):
        import concoredocker
        concoredocker.s = "new"
        concoredocker.olds = "old"

        assert concoredocker.unchanged() == False
        assert concoredocker.olds == "new"


class TestInitval:

    def test_parses_simtime_and_values(self):
        import concoredocker
        concoredocker.simtime = 0
        result = concoredocker.initval("[5.0, 1.0, 2.0]")

        assert result == [1.0, 2.0]
        assert concoredocker.simtime == 5.0

    def test_parses_single_value(self):
        import concoredocker
        concoredocker.simtime = 0
        result = concoredocker.initval("[10.0, 99]")

        assert result == [99]
        assert concoredocker.simtime == 10.0


class TestWrite:

    def test_writes_list_with_simtime(self, temp_dir):
        import concoredocker
        old_outpath = concoredocker.outpath
        outdir = os.path.join(temp_dir, "1")
        os.makedirs(outdir)
        concoredocker.outpath = temp_dir
        concoredocker.simtime = 5.0

        concoredocker.write(1, "testfile", [1.0, 2.0], delta=0)

        with open(os.path.join(outdir, "testfile")) as f:
            content = f.read()
        assert content == "[5.0, 1.0, 2.0]"
        concoredocker.outpath = old_outpath

    def test_writes_with_delta(self, temp_dir):
        import concoredocker
        old_outpath = concoredocker.outpath
        outdir = os.path.join(temp_dir, "1")
        os.makedirs(outdir)
        concoredocker.outpath = temp_dir
        concoredocker.simtime = 10.0

        concoredocker.write(1, "testfile", [3.0], delta=2)

        with open(os.path.join(outdir, "testfile")) as f:
            content = f.read()
        assert content == "[12.0, 3.0]"
        # simtime must not be mutated by write()
        assert concoredocker.simtime == 10.0
        concoredocker.outpath = old_outpath


class TestRead:

    def test_reads_and_parses_data(self, temp_dir):
        import concoredocker
        old_inpath = concoredocker.inpath
        old_delay = concoredocker.delay
        indir = os.path.join(temp_dir, "1")
        os.makedirs(indir)
        concoredocker.inpath = temp_dir
        concoredocker.delay = 0.001

        with open(os.path.join(indir, "data"), 'w') as f:
            f.write("[7.0, 100, 200]")

        concoredocker.s = ''
        concoredocker.simtime = 0
        result, ok = concoredocker.read(1, "data", "[0, 0, 0]")

        assert result == [100, 200]
        assert ok is True
        assert concoredocker.simtime == 7.0
        concoredocker.inpath = old_inpath
        concoredocker.delay = old_delay

    def test_returns_default_when_file_missing(self, temp_dir):
        import concoredocker
        old_inpath = concoredocker.inpath
        old_delay = concoredocker.delay
        indir = os.path.join(temp_dir, "1")
        os.makedirs(indir)
        concoredocker.inpath = temp_dir
        concoredocker.delay = 0.001

        concoredocker.s = ''
        concoredocker.simtime = 0
        result, ok = concoredocker.read(1, "nofile", "[0, 5, 5]")

        assert result == [5, 5]
        assert ok is False
        concoredocker.inpath = old_inpath
        concoredocker.delay = old_delay


class TestZMQ:
    @pytest.fixture(autouse=True)
    def reset_zmq_ports(self):
        import concoredocker
        original_ports = concoredocker.zmq_ports.copy()
        yield
        concoredocker.zmq_ports.clear()
        concoredocker.zmq_ports.update(original_ports)

    def test_write_prepends_simtime(self):
        import concoredocker

        class DummyPort:
            def __init__(self):
                self.sent = None

            def send_json_with_retry(self, message):
                self.sent = message

        dummy = DummyPort()
        concoredocker.zmq_ports["test_zmq"] = dummy
        concoredocker.simtime = 3.0

        concoredocker.write("test_zmq", "data", [1.0, 2.0], delta=2)

        assert dummy.sent == [5.0, 1.0, 2.0]
        # simtime must not be mutated by write()
        assert concoredocker.simtime == 3.0

    def test_read_strips_simtime(self):
        import concoredocker

        class DummyPort:
            def recv_json_with_retry(self):
                return [10.0, 4.0, 5.0]

        concoredocker.zmq_ports["test_zmq"] = DummyPort()
        concoredocker.simtime = 0

        result, ok = concoredocker.read("test_zmq", "data", "[]")

        assert result == [4.0, 5.0]
        assert ok is True
        assert concoredocker.simtime == 10.0

    def test_read_updates_simtime_monotonically(self):
        import concoredocker

        class DummyPort:
            def recv_json_with_retry(self):
                return [2.0, 99.0]

        concoredocker.zmq_ports["test_zmq"] = DummyPort()
        concoredocker.simtime = 5.0

        concoredocker.read("test_zmq", "data", "[]")

        assert concoredocker.simtime == 5.0

    def test_write_read_roundtrip(self):
        import concoredocker

        class DummyPort:
            def __init__(self):
                self.buffer = None

            def send_json_with_retry(self, message):
                self.buffer = message

            def recv_json_with_retry(self):
                return self.buffer

        dummy = DummyPort()
        concoredocker.zmq_ports["roundtrip"] = dummy
        concoredocker.simtime = 0

        original = [1.5, 2.5, 3.5]
        concoredocker.write("roundtrip", "data", original)
        result, ok = concoredocker.read("roundtrip", "data", "[]")

        assert result == original
        assert ok is True
