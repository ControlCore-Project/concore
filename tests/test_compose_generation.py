from concore_cli.commands.build import _write_docker_compose
from rich.console import Console
from pathlib import Path

def _fake_run_script(output_dir, services):
    lines = [
        f"docker run --name {s['name']} -v /study:/study {s['image']} &"
        for s in services
    ]
    (Path(output_dir) / "run").write_text("\n".join(lines))


def test_compose_has_restart_policy(tmp_path):
    _fake_run_script(tmp_path, [{"name": "node1", "image": "concore/py"}])
    path = _write_docker_compose(tmp_path, Console(quiet=True))
    assert path is not None
    content = path.read_text()
    assert "restart: on-failure" in content


def test_compose_has_network_section(tmp_path):
    _fake_run_script(tmp_path, [{"name": "node1", "image": "concore/py"}])
    path = _write_docker_compose(tmp_path, Console(quiet=True))
    content = path.read_text()
    assert "concore_net" in content
    assert "networks:" in content


def test_compose_depends_on_second_service(tmp_path):
    _fake_run_script(
        tmp_path,
        [
            {"name": "controller", "image": "concore/py"},
            {"name": "plant", "image": "concore/cpp"},
        ],
    )
    path = _write_docker_compose(tmp_path, Console(quiet=True))
    content = path.read_text()
    assert "depends_on" in content
    assert "controller" in content


def test_compose_first_service_has_no_depends_on(tmp_path):
    _fake_run_script(
        tmp_path,
        [
            {"name": "controller", "image": "concore/py"},
            {"name": "plant", "image": "concore/cpp"},
        ],
    )
    path = _write_docker_compose(tmp_path, Console(quiet=True))
    lines = path.read_text().splitlines()
    controller_idx = next(
        i for i, line in enumerate(lines) if "controller:" in line
    )
    plant_idx = next(
        i for i, line in enumerate(lines) if "plant:" in line
    )
    section = lines[controller_idx:plant_idx]
    assert not any("depends_on" in line for line in section)


def test_zmq_mode_adds_env(tmp_path):
    _fake_run_script(tmp_path, [{"name": "node1", "image": "concore/py"}])
    path = _write_docker_compose(
        tmp_path, Console(quiet=True), zmq_mode=True
    )
    content = path.read_text()
    assert "CONCORE_TRANSPORT=zmq" in content


def test_no_zmq_env_in_default_mode(tmp_path):
    _fake_run_script(tmp_path, [{"name": "node1", "image": "concore/py"}])
    path = _write_docker_compose(
        tmp_path, Console(quiet=True), zmq_mode=False
    )
    content = path.read_text()
    assert "CONCORE_TRANSPORT" not in content


def test_missing_run_script_returns_none(tmp_path):
    result = _write_docker_compose(tmp_path, Console(quiet=True))
    assert result is None


def test_zmq_without_compose_errors():
    from click.testing import CliRunner
    from concore_cli.cli import cli
    runner = CliRunner()
    result = runner.invoke(cli, ["build", "wf.graphml", "--zmq"])
    assert result.exit_code != 0
