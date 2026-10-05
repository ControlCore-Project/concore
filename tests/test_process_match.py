"""Tests for concore_cli.commands._process_match (Issue #580).

`concore stop` / `concore status` used to flag any process as a
"concore process" just because "concore" showed up somewhere in its
cmdline, which is true for basically anything launched from inside a
folder named "concore" (the default clone directory name for this
repo) and has nothing to do with a real concore node.
"""

import os

from concore_cli.commands._process_match import has_concore_markers, is_concore_process


class TestHasConcoreMarkers:
    def test_true_when_iport_and_runtime_file_present(self, tmp_path):
        (tmp_path / "concore.iport").write_text("{}")
        (tmp_path / "concore.py").write_text("")
        assert has_concore_markers(str(tmp_path)) is True

    def test_true_with_docker_runtime_file(self, tmp_path):
        (tmp_path / "concore.iport").write_text("{}")
        (tmp_path / "concoredocker.py").write_text("")
        assert has_concore_markers(str(tmp_path)) is True

    def test_false_without_iport(self, tmp_path):
        (tmp_path / "concore.py").write_text("")
        assert has_concore_markers(str(tmp_path)) is False

    def test_false_without_runtime_file(self, tmp_path):
        (tmp_path / "concore.iport").write_text("{}")
        assert has_concore_markers(str(tmp_path)) is False

    def test_false_for_empty_cwd(self):
        assert has_concore_markers(None) is False
        assert has_concore_markers("") is False

    def test_false_for_unrelated_folder_literally_named_concore(self, tmp_path):
        # A folder just happening to be named "concore" (e.g. a plain
        # git clone of this repo) is not, by itself, a running node's
        # working directory.
        concore_dir = tmp_path / "concore"
        concore_dir.mkdir()
        (concore_dir / "README.md").write_text("")
        assert has_concore_markers(str(concore_dir)) is False


class TestIsConcoreProcess:
    def test_true_for_generated_kill_script(self):
        cmdline = [r"C:\studies\run1\concorekill.bat"]
        assert is_concore_process(cmdline, cwd=None) is True

    def test_true_when_cwd_has_markers(self, tmp_path):
        (tmp_path / "concore.iport").write_text("{}")
        (tmp_path / "concore.py").write_text("")
        cmdline = ["python", "controller.py"]
        assert is_concore_process(cmdline, cwd=str(tmp_path)) is True

    def test_false_for_unrelated_process_in_a_concore_named_folder(self, tmp_path):
        # This is the actual bug: previously, having "concore" anywhere
        # in the argv (e.g. a path under a folder named "concore") was
        # enough to be treated as a concore process and get killed.
        concore_dir = tmp_path / "concore"
        concore_dir.mkdir()
        cmdline = ["node", os.path.join(str(concore_dir), "tool.js")]
        assert is_concore_process(cmdline, cwd=str(concore_dir)) is False

    def test_false_for_unrelated_python_script_mentioning_concore(self, tmp_path):
        concore_dir = tmp_path / "concore"
        concore_dir.mkdir()
        cmdline = ["python", os.path.join(str(concore_dir), "unrelated_report.py")]
        assert is_concore_process(cmdline, cwd=str(concore_dir)) is False

    def test_false_for_empty_cmdline_and_cwd(self):
        assert is_concore_process([], None) is False
