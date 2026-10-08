from pathlib import Path


def resolve_source_dir(workflow_path, source_dir):
    """Resolve --source the same way for build, validate and inspect.

    A path that exists from the current directory wins, so
    `--source demo/src` works from outside the project. Otherwise fall
    back to the folder next to the workflow, so the default `src` still
    works when the workflow is in a subdirectory.
    """
    source = Path(source_dir)
    if source.is_absolute() or source.exists():
        return source
    return Path(workflow_path).parent / source
