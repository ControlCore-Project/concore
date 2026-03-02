"""Tests for read() error signalling (Issue #390).

read() now returns (data, success_flag) and sets
concore.last_read_status / concore_base.last_read_status.
"""

import os
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class DummyZMQPort:
    """Minimal stand-in for ZeroMQPort used in ZMQ read tests."""

    def __init__(self, response=None, raise_on_recv=None):
        self._response = response
        self._raise_on_recv = raise_on_recv

    def send_json_with_retry(self, message):
        self._response = message

    def recv_json_with_retry(self):
        if self._raise_on_recv:
            raise self._raise_on_recv
        return self._response


# ---------------------------------------------------------------------------
# File-based read tests
# ---------------------------------------------------------------------------


class TestReadFileSuccess:
    """read() on a valid file returns (data, True) with SUCCESS status."""

    @pytest.fixture(autouse=True)
    def setup(self, temp_dir, monkeypatch):
        import concore

        self.concore = concore
        monkeypatch.setattr(concore, "delay", 0)

        # Create ./in1/ym with valid data: [simtime, value]
        in_dir = os.path.join(temp_dir, "in1")
        os.makedirs(in_dir, exist_ok=True)
        with open(os.path.join(in_dir, "ym"), "w") as f:
            f.write("[10, 3.14]")

        monkeypatch.setattr(concore, "inpath", os.path.join(temp_dir, "in"))

    def test_returns_data_and_true(self):
        data, ok = self.concore.read(1, "ym", "[0, 0.0]")
        assert ok is True
        assert data == [3.14]

    def test_last_read_status_is_success(self):
        self.concore.read(1, "ym", "[0, 0.0]")
        assert self.concore.last_read_status == "SUCCESS"


class TestReadFileMissing:
    """read() on a missing file returns (default, False) with FILE_NOT_FOUND."""

    @pytest.fixture(autouse=True)
    def setup(self, temp_dir, monkeypatch):
        import concore

        self.concore = concore
        monkeypatch.setattr(concore, "delay", 0)
        # Point to a directory that does NOT have the file
        monkeypatch.setattr(concore, "inpath", os.path.join(temp_dir, "in"))

    def test_returns_default_and_false(self):
        data, ok = self.concore.read(1, "nonexistent", "[0, 0.0]")
        assert ok is False

    def test_last_read_status_is_file_not_found(self):
        self.concore.read(1, "nonexistent", "[0, 0.0]")
        assert self.concore.last_read_status == "FILE_NOT_FOUND"


class TestReadFileParseError:
    """read() returns (default, False) with PARSE_ERROR on malformed content."""

    @pytest.fixture(autouse=True)
    def setup(self, temp_dir, monkeypatch):
        import concore

        self.concore = concore
        monkeypatch.setattr(concore, "delay", 0)

        in_dir = os.path.join(temp_dir, "in1")
        os.makedirs(in_dir, exist_ok=True)
        with open(os.path.join(in_dir, "ym"), "w") as f:
            f.write("NOT_VALID_PYTHON{{{")

        monkeypatch.setattr(concore, "inpath", os.path.join(temp_dir, "in"))

    def test_returns_default_and_false(self):
        data, ok = self.concore.read(1, "ym", "[0, 0.0]")
        assert ok is False

    def test_last_read_status_is_parse_error(self):
        self.concore.read(1, "ym", "[0, 0.0]")
        assert self.concore.last_read_status == "PARSE_ERROR"


class TestReadFileRetriesExceeded:
    """read() returns (default, False) with RETRIES_EXCEEDED when file is empty."""

    @pytest.fixture(autouse=True)
    def setup(self, temp_dir, monkeypatch):
        import concore

        self.concore = concore
        monkeypatch.setattr(concore, "delay", 0)

        # Create an empty file
        in_dir = os.path.join(temp_dir, "in1")
        os.makedirs(in_dir, exist_ok=True)
        with open(os.path.join(in_dir, "ym"), "w") as _f:
            pass  # empty

        monkeypatch.setattr(concore, "inpath", os.path.join(temp_dir, "in"))

    def test_returns_default_and_false(self):
        data, ok = self.concore.read(1, "ym", "[0, 0.0]")
        assert ok is False

    def test_last_read_status_is_retries_exceeded(self):
        self.concore.read(1, "ym", "[0, 0.0]")
        assert self.concore.last_read_status == "RETRIES_EXCEEDED"


# ---------------------------------------------------------------------------
# ZMQ read tests
# ---------------------------------------------------------------------------


class TestReadZMQSuccess:
    """Successful ZMQ read returns (data, True)."""

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        import concore

        self.concore = concore
        self.original_ports = concore.zmq_ports.copy()
        yield
        concore.zmq_ports.clear()
        concore.zmq_ports.update(self.original_ports)

    def test_zmq_read_returns_data_and_true(self):
        dummy = DummyZMQPort(response=[5, 1.1, 2.2])
        self.concore.zmq_ports["test_port"] = dummy
        self.concore.simtime = 0

        data, ok = self.concore.read("test_port", "ym", "[]")
        assert ok is True
        assert data == [1.1, 2.2]
        assert self.concore.last_read_status == "SUCCESS"


class TestReadZMQTimeout:
    """ZMQ read that returns None (timeout) yields (default, False)."""

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        import concore

        self.concore = concore
        self.original_ports = concore.zmq_ports.copy()
        yield
        concore.zmq_ports.clear()
        concore.zmq_ports.update(self.original_ports)

    def test_zmq_timeout_returns_default_and_false(self):
        dummy = DummyZMQPort(response=None)  # recv returns None → timeout
        self.concore.zmq_ports["test_port"] = dummy

        data, ok = self.concore.read("test_port", "ym", "[]")
        assert ok is False
        assert self.concore.last_read_status == "TIMEOUT"


class TestReadZMQError:
    """ZMQ read that raises ZMQError yields (default, False)."""

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        import concore

        self.concore = concore
        self.original_ports = concore.zmq_ports.copy()
        yield
        concore.zmq_ports.clear()
        concore.zmq_ports.update(self.original_ports)

    def test_zmq_error_returns_default_and_false(self):
        import zmq

        dummy = DummyZMQPort(raise_on_recv=zmq.error.ZMQError("test error"))
        self.concore.zmq_ports["test_port"] = dummy

        data, ok = self.concore.read("test_port", "ym", "[]")
        assert ok is False
        assert self.concore.last_read_status == "TIMEOUT"


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------


class TestReadBackwardCompatibility:
    """Legacy callers can use isinstance check on the result."""

    @pytest.fixture(autouse=True)
    def setup(self, temp_dir, monkeypatch):
        import concore

        self.concore = concore
        monkeypatch.setattr(concore, "delay", 0)

        in_dir = os.path.join(temp_dir, "in1")
        os.makedirs(in_dir, exist_ok=True)
        with open(os.path.join(in_dir, "ym"), "w") as f:
            f.write("[10, 42.0]")

        monkeypatch.setattr(concore, "inpath", os.path.join(temp_dir, "in"))

    def test_legacy_unpack_pattern(self):
        """The recommended migration pattern works correctly."""
        result = self.concore.read(1, "ym", "[0, 0.0]")

        if isinstance(result, tuple):
            value, ok = result
        else:
            value = result
            ok = True

        assert value == [42.0]
        assert ok is True

    def test_tuple_unpack(self):
        """New-style callers can unpack directly."""
        value, ok = self.concore.read(1, "ym", "[0, 0.0]")
        assert value == [42.0]
        assert ok is True


# ---------------------------------------------------------------------------
# last_read_status exposed on module
# ---------------------------------------------------------------------------


class TestLastReadStatusExposed:
    """concore.last_read_status is publicly accessible."""

    def test_attribute_exists(self):
        import concore

        assert hasattr(concore, "last_read_status")

    def test_initial_value_is_success(self):
        import concore

        # Before any read, default is SUCCESS
        assert concore.last_read_status in (
            "SUCCESS",
            "FILE_NOT_FOUND",
            "TIMEOUT",
            "PARSE_ERROR",
            "EMPTY_DATA",
            "RETRIES_EXCEEDED",
        )
