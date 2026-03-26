import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from concore_cli.cli import cli


class TestSetupCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch("concore_cli.commands.setup._resolve_concore_path")
    @patch("concore_cli.commands.setup._detect_tool")
    @patch("concore_cli.commands.setup._get_platform_key")
    def test_setup_dry_run_does_not_write(self, mock_plat, mock_detect, mock_path):
        mock_plat.return_value = "posix"
        mock_path.return_value = Path(self.temp_dir)

        def detect_side_effect(names):
            if "g++" in names:
                return "/usr/bin/g++", "g++"
            if "python3" in names:
                return "/usr/bin/python3", "python3"
            if "iverilog" in names:
                return "/usr/bin/iverilog", "iverilog"
            if "octave" in names:
                return "/usr/bin/octave", "octave"
            if "docker" in names:
                return "/usr/bin/docker", "docker"
            return None, None

        mock_detect.side_effect = detect_side_effect

        result = self.runner.invoke(cli, ["setup", "--dry-run"])
        self.assertEqual(result.exit_code, 0)

        self.assertFalse((Path(self.temp_dir) / "concore.tools").exists())
        self.assertFalse((Path(self.temp_dir) / "concore.sudo").exists())
        self.assertFalse((Path(self.temp_dir) / "concore.octave").exists())

    @patch("concore_cli.commands.setup._resolve_concore_path")
    @patch("concore_cli.commands.setup._detect_tool")
    @patch("concore_cli.commands.setup._get_platform_key")
    def test_setup_writes_files(self, mock_plat, mock_detect, mock_path):
        mock_plat.return_value = "posix"
        mock_path.return_value = Path(self.temp_dir)

        def detect_side_effect(names):
            if "g++" in names:
                return "/usr/bin/g++", "g++"
            if "python3" in names:
                return "/usr/bin/python3", "python3"
            if "iverilog" in names:
                return "/usr/bin/iverilog", "iverilog"
            if "octave" in names:
                return "/usr/bin/octave", "octave"
            if "docker" in names:
                return "/usr/bin/docker", "docker"
            return None, None

        mock_detect.side_effect = detect_side_effect

        result = self.runner.invoke(cli, ["setup"])
        self.assertEqual(result.exit_code, 0)

        tools_file = Path(self.temp_dir) / "concore.tools"
        sudo_file = Path(self.temp_dir) / "concore.sudo"
        octave_file = Path(self.temp_dir) / "concore.octave"

        self.assertTrue(tools_file.exists())
        self.assertTrue(sudo_file.exists())
        self.assertTrue(octave_file.exists())

        tools_content = tools_file.read_text()
        self.assertIn("CPPEXE=/usr/bin/g++", tools_content)
        self.assertIn("PYTHONEXE=/usr/bin/python3", tools_content)
        self.assertIn("VEXE=/usr/bin/iverilog", tools_content)
        self.assertIn("OCTAVEEXE=/usr/bin/octave", tools_content)
        self.assertEqual(sudo_file.read_text().strip(), "docker")

    @patch("concore_cli.commands.setup._resolve_concore_path")
    @patch("concore_cli.commands.setup._detect_tool")
    @patch("concore_cli.commands.setup._get_platform_key")
    def test_setup_no_force_keeps_existing(self, mock_plat, mock_detect, mock_path):
        mock_plat.return_value = "posix"
        mock_path.return_value = Path(self.temp_dir)

        tools_file = Path(self.temp_dir) / "concore.tools"
        tools_file.write_text("CPPEXE=/old/path\n")

        def detect_side_effect(names):
            if "g++" in names:
                return "/usr/bin/g++", "g++"
            if "python3" in names:
                return "/usr/bin/python3", "python3"
            return None, None

        mock_detect.side_effect = detect_side_effect

        result = self.runner.invoke(cli, ["setup"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(tools_file.read_text(), "CPPEXE=/old/path\n")

    @patch("concore_cli.commands.setup._resolve_concore_path")
    @patch("concore_cli.commands.setup._detect_tool")
    @patch("concore_cli.commands.setup._get_platform_key")
    def test_setup_force_overwrites_existing(self, mock_plat, mock_detect, mock_path):
        mock_plat.return_value = "posix"
        mock_path.return_value = Path(self.temp_dir)

        tools_file = Path(self.temp_dir) / "concore.tools"
        tools_file.write_text("CPPEXE=/old/path\n")

        def detect_side_effect(names):
            if "g++" in names:
                return "/usr/bin/g++", "g++"
            if "python3" in names:
                return "/usr/bin/python3", "python3"
            return None, None

        mock_detect.side_effect = detect_side_effect

        result = self.runner.invoke(cli, ["setup", "--force"])
        self.assertEqual(result.exit_code, 0)

        content = tools_file.read_text()
        self.assertIn("CPPEXE=/usr/bin/g++", content)
        self.assertIn("PYTHONEXE=/usr/bin/python3", content)


if __name__ == "__main__":
    unittest.main()
