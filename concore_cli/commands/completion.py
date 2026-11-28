from click.shell_completion import get_completion_class

SHELLS = ("bash", "zsh", "fish")
PROG_NAME = "concore"
COMPLETE_VAR = "_CONCORE_COMPLETE"


def completion_script(cli, shell):
    """Return the shell completion script for the concore command."""
    completion_class = get_completion_class(shell)
    if completion_class is None:
        raise ValueError(f"Unsupported shell '{shell}' (use bash, zsh or fish)")
    return completion_class(cli, {}, PROG_NAME, COMPLETE_VAR).source()
