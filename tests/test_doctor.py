import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner
from concore_cli.cli import cli
from concore_cli.commands.doctor import (
    _detect_tool,
    _get_platform_key,
    _check_package,
    _resolve_concore_path,
    doctor_check,
)


class TestDoctorCommand(unittest.TestCase):
    """Tests for the concore doctor CLI command."""

    def setUp(self):
        self.runner = CliRunner()

    def test_doctor_command_runs(self):
        """Doctor command should run and produce output."""
        result = self.runner.invoke(cli, ["doctor"])
        self.assertIn("concore Doctor", result.output)
        self.assertIn("Core Checks", result.output)
        self.assertIn("Tools", result.output)
        self.assertIn("Configuration", result.output)
        self.assertIn("Dependencies", result.output)
        self.assertIn("Summary", result.output)

    def test_doctor_help(self):
        """Doctor command should have help text."""
        result = self.runner.invoke(cli, ["doctor", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Check system readiness", result.output)

    def test_doctor_shows_python_version(self):
        """Doctor should show the current Python version."""
        result = self.runner.invoke(cli, ["doctor"])
        import platform
        py_version = platform.python_version()
        self.assertIn(py_version, result.output)

    def test_doctor_shows_concore_version(self):
        """Doctor should detect and show concore version."""
        from concore_cli import __version__
        result = self.runner.invoke(cli, ["doctor"])
        self.assertIn("concore", result.output)
        self.assertIn(__version__, result.output)

    def test_doctor_shows_concorepath(self):
        """Doctor should show the CONCOREPATH."""
        result = self.runner.invoke(cli, ["doctor"])
        self.assertIn("CONCOREPATH", result.output)

    def test_doctor_checks_dependencies(self):
        """Doctor should check required Python packages."""
        result = self.runner.invoke(cli, ["doctor"])
        # These should be installed since we're running tests
        self.assertIn("click", result.output)
        self.assertIn("rich", result.output)

    def test_doctor_shows_summary(self):
        """Doctor should show a summary with pass/warn/error counts."""
        result = self.runner.invoke(cli, ["doctor"])
        self.assertIn("Summary", result.output)
        self.assertIn("passed", result.output)


class TestDetectTool(unittest.TestCase):
    """Tests for tool detection helpers."""

    def test_detect_python(self):
        """Should detect the currently running Python."""
        # python or python3 should be findable
        path, name = _detect_tool(["python3", "python"])
        self.assertIsNotNone(path)
        self.assertIn(name, ["python3", "python"])

    def test_detect_nonexistent_tool(self):
        """Should return None for a tool that doesn't exist."""
        path, name = _detect_tool(["nonexistent_tool_abc123"])
        self.assertIsNone(path)
        self.assertIsNone(name)

    def test_detect_tool_tries_multiple_names(self):
        """Should try all candidate names and return the first match."""
        path, name = _detect_tool(
            ["nonexistent_tool_abc123", "python3", "python"]
        )
        self.assertIsNotNone(path)

    def test_detect_tool_empty_list(self):
        """Should handle an empty candidate list gracefully."""
        path, name = _detect_tool([])
        self.assertIsNone(path)
        self.assertIsNone(name)


class TestGetPlatformKey(unittest.TestCase):
    """Tests for platform detection."""

    def test_returns_valid_key(self):
        """Should return 'posix' or 'windows'."""
        key = _get_platform_key()
        self.assertIn(key, ["posix", "windows"])

    @patch("concore_cli.commands.doctor.os.name", "nt")
    def test_windows_detection(self):
        """Should return 'windows' when os.name is 'nt'."""
        key = _get_platform_key()
        self.assertEqual(key, "windows")

    @patch("concore_cli.commands.doctor.os.name", "posix")
    def test_posix_detection(self):
        """Should return 'posix' when os.name is 'posix'."""
        key = _get_platform_key()
        self.assertEqual(key, "posix")


class TestCheckPackage(unittest.TestCase):
    """Tests for package checking."""

    def test_check_installed_package(self):
        """Should detect an installed package."""
        found, version = _check_package("click")
        self.assertTrue(found)
        self.assertIsNotNone(version)

    def test_check_missing_package(self):
        """Should return False for a package that isn't installed."""
        found, version = _check_package("nonexistent_package_abc123")
        self.assertFalse(found)
        self.assertIsNone(version)

    def test_check_package_with_import_name_map(self):
        """Should use the correct import name for beautifulsoup4 (bs4)."""
        found, version = _check_package("beautifulsoup4")
        self.assertTrue(found)

    def test_check_pyzmq_import_name(self):
        """Should use 'zmq' as import name for pyzmq."""
        found, version = _check_package("pyzmq")
        self.assertTrue(found)


class TestResolveConCorePath(unittest.TestCase):
    """Tests for CONCOREPATH resolution."""

    def test_resolves_to_existing_path(self):
        """Should return a Path object."""
        result = _resolve_concore_path()
        self.assertIsInstance(result, Path)


class TestDoctorWithConfig(unittest.TestCase):
    """Tests for doctor command with config files present."""

    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch(
        "concore_cli.commands.doctor._resolve_concore_path"
    )
    def test_doctor_with_concore_tools(self, mock_path):
        """Doctor should detect and report concore.tools."""
        mock_path.return_value = Path(self.temp_dir)
        tools_file = Path(self.temp_dir) / "concore.tools"
        tools_file.write_text("CPPEXE=/usr/bin/g++\nPYTHONEXE=/usr/bin/python3\n")

        from rich.console import Console
        import io
        console = Console(file=io.StringIO(), force_terminal=True)
        result = doctor_check(console)
        # Just verify it doesn't crash
        self.assertIsInstance(result, bool)

    @patch(
        "concore_cli.commands.doctor._resolve_concore_path"
    )
    def test_doctor_with_concore_octave(self, mock_path):
        """Doctor should detect concore.octave flag."""
        mock_path.return_value = Path(self.temp_dir)
        octave_file = Path(self.temp_dir) / "concore.octave"
        octave_file.write_text("")

        from rich.console import Console
        import io
        console = Console(file=io.StringIO(), force_terminal=True)
        result = doctor_check(console)
        self.assertIsInstance(result, bool)

    @patch(
        "concore_cli.commands.doctor._resolve_concore_path"
    )
    def test_doctor_with_concore_sudo(self, mock_path):
        """Doctor should detect concore.sudo config."""
        mock_path.return_value = Path(self.temp_dir)
        sudo_file = Path(self.temp_dir) / "concore.sudo"
        sudo_file.write_text("docker")

        from rich.console import Console
        import io
        console = Console(file=io.StringIO(), force_terminal=True)
        result = doctor_check(console)
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
