import json
import os
from ast import literal_eval

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def reset_state():
    import concore

    old_simtime = concore.simtime
    old_outpath = concore.outpath
    original_ports = concore.zmq_ports.copy()
    yield
    concore.simtime = old_simtime
    concore.outpath = old_outpath
    concore.zmq_ports.clear()
    concore.zmq_ports.update(original_ports)


def _write_and_read_file(temp_dir, val):
    import concore

    concore.simtime = 5
    os.makedirs(os.path.join(temp_dir, "out1"), exist_ok=True)
    concore.outpath = os.path.join(temp_dir, "out")
    concore.write(1, "data", val)
    path = os.path.join(temp_dir, "out1", "data")
    assert os.path.exists(path), "write() produced no file"
    with open(path) as f:
        return f.read()


def test_file_write_bare_array(temp_dir):
    assert _write_and_read_file(temp_dir, np.array([1.5, 2.0])) == "[5, 1.5, 2.0]"


def test_file_write_array_inside_list_is_readable(temp_dir):
    text = _write_and_read_file(temp_dir, [np.array([1, 2]), 3.0])
    assert "array" not in text
    assert literal_eval(text) == [5, [1, 2], 3.0]


def test_file_write_two_dimensional_array(temp_dir):
    text = _write_and_read_file(temp_dir, [np.zeros((2, 2))])
    assert literal_eval(text) == [5, [[0.0, 0.0], [0.0, 0.0]]]


def test_convert_numpy_to_python_handles_arrays():
    from concore import convert_numpy_to_python

    result = convert_numpy_to_python({"a": np.array([1, 2]), "b": [np.int64(3)]})
    assert result == {"a": [1, 2], "b": [3]}
    assert type(result["a"][0]) is int


def test_zmq_write_array_is_json_serializable():
    import concore

    class DummyZMQPort:
        def __init__(self):
            self.buffer = None

        def send_json_with_retry(self, message):
            self.buffer = message

    dummy = DummyZMQPort()
    concore.zmq_ports["np_test"] = dummy
    concore.simtime = 2
    concore.write("np_test", "data", [np.array([1.0, 2.0]), np.float32(0.5)])

    assert dummy.buffer == [2, [1.0, 2.0], 0.5]
    json.dumps(dummy.buffer)
