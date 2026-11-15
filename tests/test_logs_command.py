import threading
import time

from click.testing import CliRunner

from concore_cli.cli import cli


def _study(tmp_path, nodes):
    study = tmp_path / "study"
    (study / "src").mkdir(parents=True)
    for name, text in nodes.items():
        node = study / name
        (node / "in1").mkdir(parents=True)
        (node / "out1").mkdir()
        if text is not None:
            (node / "concoreout.txt").write_text(text)
    return study


def test_logs_shows_every_node(tmp_path):
    study = _study(tmp_path, {"CZ": "a1\na2\n", "PZ": "b1\n"})
    result = CliRunner().invoke(cli, ["logs", str(study)])
    assert result.exit_code == 0
    assert "== CZ ==" in result.output and "[CZ] a2" in result.output
    assert "== PZ ==" in result.output and "[PZ] b1" in result.output


def test_logs_single_node_has_no_prefix(tmp_path):
    study = _study(tmp_path, {"CZ": "a1\na2\n", "PZ": "b1\n"})
    result = CliRunner().invoke(cli, ["logs", str(study), "CZ"])
    assert result.exit_code == 0
    assert "a2" in result.output
    assert "b1" not in result.output
    assert "[CZ]" not in result.output


def test_logs_lines_limits_output(tmp_path):
    study = _study(tmp_path, {"CZ": "".join(f"line{i}\n" for i in range(50))})
    result = CliRunner().invoke(cli, ["logs", str(study), "CZ", "-n", "3"])
    assert result.exit_code == 0
    assert "line49" in result.output and "line47" in result.output
    assert "line46" not in result.output


def test_logs_does_not_interpret_markup(tmp_path):
    study = _study(tmp_path, {"CZ": "value [red]x[/red] [1, 2]\n"})
    result = CliRunner().invoke(cli, ["logs", str(study), "CZ"])
    assert result.exit_code == 0
    assert "[red]x[/red] [1, 2]" in result.output


def test_logs_unknown_node_lists_known_nodes(tmp_path):
    study = _study(tmp_path, {"CZ": "a\n"})
    result = CliRunner().invoke(cli, ["logs", str(study), "NOPE"])
    assert result.exit_code == 1
    assert "NOPE" in result.output and "CZ" in result.output


def test_logs_before_first_run_is_not_an_error(tmp_path):
    study = _study(tmp_path, {"CZ": None})
    result = CliRunner().invoke(cli, ["logs", str(study)])
    assert result.exit_code == 0
    assert "No concoreout.txt found" in result.output


def test_logs_missing_directory(tmp_path):
    result = CliRunner().invoke(cli, ["logs", str(tmp_path / "nope")])
    assert result.exit_code != 0


def test_logs_follow_prints_new_lines(tmp_path, monkeypatch):
    study = _study(tmp_path, {"CZ": "old\n"})
    log = study / "CZ" / "concoreout.txt"

    def append_then_stop():
        time.sleep(0.3)
        with open(log, "a") as f:
            f.write("new1\nnew2\n")
        time.sleep(0.2)

    real_sleep = time.sleep
    calls = {"n": 0}

    def fake_sleep(seconds):
        calls["n"] += 1
        if calls["n"] > 4:
            raise KeyboardInterrupt
        real_sleep(0.2)

    monkeypatch.setattr("concore_cli.commands.logs.time.sleep", fake_sleep)
    t = threading.Thread(target=append_then_stop)
    t.start()
    result = CliRunner().invoke(cli, ["logs", str(study), "CZ", "-f"])
    t.join()
    assert result.exit_code == 0
    assert "old" in result.output
    assert "new1" in result.output and "new2" in result.output
