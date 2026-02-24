import pytest
import os
import sys
import numpy as np


# ===================================================================
# PID Registry Tests (Issue #391)
# ===================================================================

class TestPidRegistry:
    """Tests for the Windows PID registry mechanism that replaces the
    old single-overwrite concorekill.bat approach."""

    @pytest.fixture(autouse=True)
    def use_temp_dir(self, temp_dir, monkeypatch):
        """Run each test in an isolated temp directory."""
        self.temp_dir = temp_dir
        monkeypatch.chdir(temp_dir)

    def test_register_pid_creates_registry_file(self):
        """_register_pid should create concorekill_pids.txt with current PID."""
        from concore import _register_pid, _PID_REGISTRY_FILE
        _register_pid()
        assert os.path.exists(_PID_REGISTRY_FILE)
        with open(_PID_REGISTRY_FILE) as f:
            pids = [line.strip() for line in f if line.strip()]
        assert str(os.getpid()) in pids

    def test_register_pid_appends_not_overwrites(self):
        """Multiple calls to _register_pid should append, not overwrite."""
        from concore import _register_pid, _PID_REGISTRY_FILE
        # Simulate two different PIDs by writing manually then registering
        with open(_PID_REGISTRY_FILE, "w") as f:
            f.write("11111\n")
            f.write("22222\n")
        _register_pid()
        with open(_PID_REGISTRY_FILE) as f:
            pids = [line.strip() for line in f if line.strip()]
        assert "11111" in pids
        assert "22222" in pids
        assert str(os.getpid()) in pids
        assert len(pids) == 3

    def test_cleanup_pid_removes_current_pid(self):
        """_cleanup_pid should remove only the current PID from the registry."""
        from concore import _cleanup_pid, _PID_REGISTRY_FILE
        current_pid = str(os.getpid())
        with open(_PID_REGISTRY_FILE, "w") as f:
            f.write("99999\n")
            f.write(current_pid + "\n")
            f.write("88888\n")
        _cleanup_pid()
        with open(_PID_REGISTRY_FILE) as f:
            pids = [line.strip() for line in f if line.strip()]
        assert current_pid not in pids
        assert "99999" in pids
        assert "88888" in pids

    def test_cleanup_pid_deletes_files_when_last_pid(self):
        """When the current PID is the only one left, cleanup should
        remove both the registry file and the kill script."""
        from concore import _cleanup_pid, _PID_REGISTRY_FILE, _KILL_SCRIPT_FILE
        current_pid = str(os.getpid())
        with open(_PID_REGISTRY_FILE, "w") as f:
            f.write(current_pid + "\n")
        # Create a dummy kill script to verify it gets cleaned up
        with open(_KILL_SCRIPT_FILE, "w") as f:
            f.write("@echo off\n")
        _cleanup_pid()
        assert not os.path.exists(_PID_REGISTRY_FILE)
        assert not os.path.exists(_KILL_SCRIPT_FILE)

    def test_cleanup_pid_handles_missing_registry(self):
        """_cleanup_pid should not crash when registry file doesn't exist."""
        from concore import _cleanup_pid, _PID_REGISTRY_FILE
        assert not os.path.exists(_PID_REGISTRY_FILE)
        _cleanup_pid()  # Should not raise

    def test_write_kill_script_generates_bat_file(self):
        """_write_kill_script should create concorekill.bat with validation logic."""
        from concore import _write_kill_script, _KILL_SCRIPT_FILE, _PID_REGISTRY_FILE
        _write_kill_script()
        assert os.path.exists(_KILL_SCRIPT_FILE)
        with open(_KILL_SCRIPT_FILE) as f:
            content = f.read()
        # Script should reference the PID registry file
        assert _PID_REGISTRY_FILE in content
        # Script should validate processes before killing
        assert "tasklist" in content
        assert "taskkill" in content
        assert "python" in content.lower()

    def test_multi_node_registration(self):
        """Simulate 3 nodes registering PIDs — all should be present."""
        from concore import _register_pid, _PID_REGISTRY_FILE
        fake_pids = ["1204", "1932", "8120"]
        with open(_PID_REGISTRY_FILE, "w") as f:
            for pid in fake_pids:
                f.write(pid + "\n")
        _register_pid()  # Current process is the 4th
        with open(_PID_REGISTRY_FILE) as f:
            pids = [line.strip() for line in f if line.strip()]
        for pid in fake_pids:
            assert pid in pids
        assert str(os.getpid()) in pids
        assert len(pids) == 4

    def test_cleanup_preserves_other_pids(self):
        """After cleanup, only the current process PID should be removed."""
        from concore import _cleanup_pid, _PID_REGISTRY_FILE
        current_pid = str(os.getpid())
        other_pids = ["1111", "2222", "3333"]
        with open(_PID_REGISTRY_FILE, "w") as f:
            for pid in other_pids:
                f.write(pid + "\n")
            f.write(current_pid + "\n")
        _cleanup_pid()
        with open(_PID_REGISTRY_FILE) as f:
            pids = [line.strip() for line in f if line.strip()]
        assert len(pids) == 3
        assert current_pid not in pids
        for pid in other_pids:
            assert pid in pids

    @pytest.mark.skipif(not hasattr(sys, 'getwindowsversion'),
                        reason="Windows-only test")
    def test_import_registers_pid_on_windows(self):
        """On Windows, importing concore should register the PID."""
        from concore import _PID_REGISTRY_FILE
        # The import already happened, so just verify the registry exists
        # in our temp dir (we can't easily test the import-time side effect
        # since concore was already imported — we test the functions directly)
        from concore import _register_pid
        _register_pid()
        assert os.path.exists(_PID_REGISTRY_FILE)


class TestSafeLiteralEval:
    def test_reads_dictionary_from_file(self, temp_dir):
        test_file = os.path.join(temp_dir, "config.txt")
        with open(test_file, "w") as f:
            f.write("{'name': 'test', 'value': 123}")

        from concore import safe_literal_eval

        result = safe_literal_eval(test_file, {})

        assert result == {"name": "test", "value": 123}

    def test_returns_default_when_file_missing(self):
        from concore import safe_literal_eval

        result = safe_literal_eval("nonexistent_file.txt", "fallback")

        assert result == "fallback"

    def test_returns_default_for_empty_file(self, temp_dir):
        test_file = os.path.join(temp_dir, "empty.txt")
        with open(test_file, "w") as _:
            pass

        from concore import safe_literal_eval

        result = safe_literal_eval(test_file, "default")

        assert result == "default"


class TestTryparam:
    @pytest.fixture(autouse=True)
    def reset_params(self):
        from concore import params

        original_params = params.copy()
        yield
        params.clear()
        params.update(original_params)

    def test_returns_existing_parameter(self):
        from concore import tryparam, params

        params["my_setting"] = "custom_value"

        result = tryparam("my_setting", "default_value")

        assert result == "custom_value"

    def test_returns_default_for_missing_parameter(self):
        from concore import tryparam

        result = tryparam("missing_param", "fallback")

        assert result == "fallback"


class TestZeroMQPort:
    def test_class_is_defined(self):
        from concore import ZeroMQPort

        assert ZeroMQPort is not None


class TestDefaultConfiguration:
    def test_default_input_path(self):
        from concore import inpath

        assert inpath == "./in"

    def test_default_output_path(self):
        from concore import outpath

        assert outpath == "./out"


class TestPublicAPI:
    def test_module_imports_successfully(self):
        from concore import safe_literal_eval

        assert safe_literal_eval is not None

    def test_core_functions_exist(self):
        from concore import safe_literal_eval, tryparam, default_maxtime

        assert callable(safe_literal_eval)
        assert callable(tryparam)
        assert callable(default_maxtime)


class TestNumpyConversion:
    def test_convert_scalar(self):
        from concore import convert_numpy_to_python

        val = np.float64(3.14)
        res = convert_numpy_to_python(val)
        assert type(res) == float
        assert res == 3.14

    def test_convert_list_and_dict(self):
        from concore import convert_numpy_to_python

        data = {"a": np.int32(10), "b": [np.float64(1.1), np.float64(2.2)]}
        res = convert_numpy_to_python(data)
        assert type(res["a"]) == int
        assert type(res["b"][0]) == float
        assert res["b"][1] == 2.2


class TestInitVal:
    @pytest.fixture(autouse=True)
    def reset_simtime(self):
        import concore

        old_simtime = concore.simtime
        yield
        concore.simtime = old_simtime

    def test_initval_updates_simtime(self):
        import concore

        concore.simtime = 0
        # initval takes string repr of a list [time, val1, val2...]
        result = concore.initval("[100, 'data']")

        assert concore.simtime == 100
        assert result == ["data"]

    def test_initval_handles_bad_input(self):
        import concore

        concore.simtime = 0
        # Input that isn't a list
        result = concore.initval("not_a_list")
        assert concore.simtime == 0
        assert result == []


class TestDefaultMaxTime:
    def test_uses_file_value(self, temp_dir, monkeypatch):
        import concore

        # Mock the path to maxtime file
        maxtime_file = os.path.join(temp_dir, "concore.maxtime")
        with open(maxtime_file, "w") as f:
            f.write("500")

        monkeypatch.setattr(concore, "concore_maxtime_file", maxtime_file)
        concore.default_maxtime(100)

        assert concore.maxtime == 500

    def test_uses_default_when_missing(self, monkeypatch):
        import concore

        monkeypatch.setattr(concore, "concore_maxtime_file", "missing_file")
        concore.default_maxtime(999)
        assert concore.maxtime == 999


class TestUnchanged:
    @pytest.fixture(autouse=True)
    def reset_globals(self):
        import concore

        old_s = concore.s
        old_olds = concore.olds
        yield
        concore.s = old_s
        concore.olds = old_olds

    def test_unchanged_returns_true_if_same(self):
        import concore

        concore.s = "same"
        concore.olds = "same"

        # Should return True and reset s to empty
        assert concore.unchanged() is True
        assert concore.s == ""

    def test_unchanged_returns_false_if_diff(self):
        import concore

        concore.s = "new"
        concore.olds = "old"

        assert concore.unchanged() is False
        assert concore.olds == "new"


class TestParseParams:
    def test_simple_key_value_pairs(self):
        from concore import parse_params

        params = parse_params("a=1;b=2")
        assert params == {"a": 1, "b": 2}

    def test_preserves_whitespace_in_values(self):
        from concore import parse_params

        params = parse_params("label = hello world ; x = 5")
        assert params["label"] == "hello world"
        assert params["x"] == 5

    def test_embedded_equals_in_value(self):
        from concore import parse_params

        params = parse_params("url=https://example.com?a=1&b=2")
        assert params["url"] == "https://example.com?a=1&b=2"

    def test_numeric_and_list_coercion(self):
        from concore import parse_params

        params = parse_params("delay=5;coeffs=[1,2,3]")
        assert params["delay"] == 5
        assert params["coeffs"] == [1, 2, 3]

    def test_dict_literal_backward_compatibility(self):
        from concore import parse_params

        params = parse_params("{'a': 1, 'b': 2}")
        assert params == {"a": 1, "b": 2}

    def test_windows_quoted_input(self):
        from concore import parse_params

        s = '"a=1;b=2"'
        s = s[1:-1]  # simulate quote stripping before parse_params
        params = parse_params(s)
        assert params == {"a": 1, "b": 2}


class TestWriteZMQ:
    @pytest.fixture(autouse=True)
    def reset_zmq_ports(self):
        import concore

        original_ports = concore.zmq_ports.copy()
        yield
        concore.zmq_ports.clear()
        concore.zmq_ports.update(original_ports)

    def test_write_converts_numpy_types_for_zmq(self):
        import concore

        class DummyPort:
            def __init__(self):
                self.sent = None

            def send_json_with_retry(self, message):
                self.sent = message

        dummy = DummyPort()
        concore.zmq_ports["test_zmq"] = dummy

        # Reset simtime for predictable test behavior
        concore.simtime = 0

        payload = [np.int64(7), np.float64(3.5), {"x": np.float32(1.25)}]
        concore.write("test_zmq", "data", payload)

        assert dummy.sent is not None
        # ZMQ write now prepends simtime (0 in this case) to match file-based write behavior
        assert dummy.sent == [0, 7, 3.5, {"x": 1.25}]
        # Data values (after simtime) should be converted from numpy types
        assert not isinstance(dummy.sent[1], np.generic)
        assert not isinstance(dummy.sent[2], np.generic)
        assert not isinstance(dummy.sent[3]["x"], np.generic)

    def test_zmq_write_read_roundtrip(self):
        """Test that ZMQ write+read returns original data without simtime prefix."""
        import concore

        class DummyZMQPort:
            def __init__(self):
                self.buffer = None

            def send_json_with_retry(self, message):
                self.buffer = message

            def recv_json_with_retry(self):
                return self.buffer

        dummy = DummyZMQPort()
        concore.zmq_ports["roundtrip_test"] = dummy

        # Reset simtime for predictable test behavior
        concore.simtime = 0

        original_data = [1.5, 2.5, 3.5]
        concore.write("roundtrip_test", "data", original_data)

        # Read should return original data (simtime stripped) plus success flag
        result, ok = concore.read("roundtrip_test", "data", "[]")
        assert result == original_data
        assert ok is True


class TestSimtimeNotMutatedByWrite:
    """Regression tests for issue #385:
    write() must NOT mutate global simtime. Simtime advancement happens
    only in read() via max(simtime, file_simtime). Mutating simtime in
    write() causes cascading timestamps in multi-output-port nodes and
    breaks cross-language determinism.
    """

    @pytest.fixture(autouse=True)
    def reset_simtime(self):
        import concore

        old_simtime = concore.simtime
        yield
        concore.simtime = old_simtime

    @pytest.fixture(autouse=True)
    def reset_outpath(self):
        import concore

        old_outpath = concore.outpath
        yield
        concore.outpath = old_outpath

    @pytest.fixture(autouse=True)
    def reset_zmq_ports(self):
        import concore

        original_ports = concore.zmq_ports.copy()
        yield
        concore.zmq_ports.clear()
        concore.zmq_ports.update(original_ports)

    # ---- Test Case 1: single-output write keeps simtime unchanged ----

    def test_single_file_write_does_not_mutate_simtime(self, temp_dir):
        """A single file-based write with delta must not change simtime."""
        import concore

        concore.simtime = 10
        out_dir = os.path.join(temp_dir, "out1")
        os.makedirs(out_dir, exist_ok=True)
        concore.outpath = os.path.join(temp_dir, "out")

        concore.write(1, "v", [5.0], delta=1)

        assert concore.simtime == 10, (
            "simtime must not be mutated by write(); "
            "was %s instead of 10" % concore.simtime
        )

    def test_single_zmq_write_does_not_mutate_simtime(self):
        """A single ZMQ-based write with delta must not change simtime."""
        import concore

        class DummyPort:
            def send_json_with_retry(self, msg):
                self.sent = msg

        dummy = DummyPort()
        concore.zmq_ports["zmq_test"] = dummy
        concore.simtime = 10

        concore.write("zmq_test", "v", [5.0], delta=1)

        assert concore.simtime == 10, (
            "simtime must not be mutated by ZMQ write(); "
            "was %s instead of 10" % concore.simtime
        )

    # ---- Test Case 2: multi-port write → identical timestamps ----

    def test_multi_port_file_writes_share_same_timestamp(self, temp_dir):
        """Two consecutive file writes with delta=1 must produce the
        same timestamp (simtime+delta), proving simtime is not incremented
        between calls."""
        import concore

        concore.simtime = 10
        concore.outpath = os.path.join(temp_dir, "out")
        for p in (1, 2):
            os.makedirs(os.path.join(temp_dir, "out" + str(p)), exist_ok=True)

        concore.write(1, "u", [1.0], delta=1)
        concore.write(2, "v", [2.0], delta=1)

        # Read back the written files and compare timestamps
        from ast import literal_eval

        payloads = []
        for p in (1, 2):
            with open(
                os.path.join(temp_dir, "out" + str(p), ("u" if p == 1 else "v"))
            ) as f:
                payloads.append(literal_eval(f.read()))

        ts1, ts2 = payloads[0][0], payloads[1][0]
        assert ts1 == ts2 == 11, (
            "Both ports must share timestamp simtime+delta=11; "
            "got %s and %s" % (ts1, ts2)
        )

    def test_multi_port_zmq_writes_share_same_timestamp(self):
        """Two consecutive ZMQ writes with delta=1 must produce the
        same timestamp."""
        import concore

        class DummyPort:
            def __init__(self):
                self.sent = None

            def send_json_with_retry(self, msg):
                self.sent = msg

        d1, d2 = DummyPort(), DummyPort()
        concore.zmq_ports["p1"] = d1
        concore.zmq_ports["p2"] = d2
        concore.simtime = 10

        concore.write("p1", "u", [1.0], delta=1)
        concore.write("p2", "v", [2.0], delta=1)

        assert d1.sent[0] == d2.sent[0] == 11, (
            "Both ZMQ ports must share timestamp 11; got %s and %s"
            % (d1.sent[0], d2.sent[0])
        )

    # ---- Test Case 3: cross-language parity check ----

    def test_write_timestamp_matches_cpp_semantics(self, temp_dir):
        """C++ uses `simtime+delta` as a local expression without mutation.
        After N writes with delta=1, simtime must still be the original
        value — matching C++ behaviour."""
        import concore

        concore.simtime = 0
        concore.outpath = os.path.join(temp_dir, "out")
        for p in range(1, 4):
            os.makedirs(os.path.join(temp_dir, "out" + str(p)), exist_ok=True)

        for p in range(1, 4):
            concore.write(p, "x", [float(p)], delta=1)

        assert concore.simtime == 0, (
            "After 3 writes with delta=1 simtime must remain 0 "
            "(matching C++/MATLAB/Verilog); got %s" % concore.simtime
        )
