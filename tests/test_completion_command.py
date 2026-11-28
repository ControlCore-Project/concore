import pytest
from click.shell_completion import get_completion_class
from click.testing import CliRunner

from concore_cli.cli import cli


@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
def test_completion_prints_script_for_each_shell(shell):
    result = CliRunner().invoke(cli, ["completion", shell])
    assert result.exit_code == 0
    assert "_CONCORE_COMPLETE" in result.output
    assert "concore" in result.output


def test_completion_rejects_unknown_shell():
    result = CliRunner().invoke(cli, ["completion", "powershell"])
    assert result.exit_code != 0


def _complete(args, incomplete):
    comp = get_completion_class("bash")(cli, {}, "concore", "_CONCORE_COMPLETE")
    return [item.value for item in comp.get_completions(args, incomplete)]


def test_commands_are_completed():
    assert _complete([], "va") == ["validate"]
    assert "completion" in _complete([], "")


def test_option_values_are_completed():
    assert _complete(["build", "wf.graphml", "--type"], "") == [
        "windows",
        "posix",
        "docker",
    ]


def test_completion_command_completes_shell_names():
    assert _complete(["completion"], "") == ["bash", "zsh", "fish"]
