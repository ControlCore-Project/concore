import shutil
import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from concore_cli.cli import cli


class TestBuildForce(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _project(self):
        result = self.runner.invoke(cli, ["init", "proj"])
        self.assertEqual(result.exit_code, 0, result.output)
        return [
            "build",
            "proj/workflow.graphml",
            "--source",
            "proj/src",
            "--type",
            "posix",
        ]

    def test_existing_output_is_an_error_without_force(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            args = self._project()
            Path("out").mkdir()
            (Path("out") / "keep.txt").write_text("x")

            result = self.runner.invoke(cli, args + ["--output", "out"])

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("already exists", result.output)
            self.assertIn("--force", result.output)
            self.assertTrue((Path("out") / "keep.txt").exists())

    def test_force_replaces_a_generated_study(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            args = self._project()
            first = self.runner.invoke(cli, args + ["--output", "out"])
            self.assertEqual(first.exit_code, 0, first.output)
            (Path("out") / "stale.txt").write_text("old")

            second = self.runner.invoke(cli, args + ["--output", "out", "--force"])

            self.assertEqual(second.exit_code, 0, second.output)
            self.assertFalse((Path("out") / "stale.txt").exists())
            self.assertTrue((Path("out") / "run").exists())

    def test_force_refuses_a_directory_that_is_not_a_study(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            args = self._project()
            Path("mydata").mkdir()
            (Path("mydata") / "important.txt").write_text("keep me")

            result = self.runner.invoke(cli, args + ["--output", "mydata", "--force"])

            self.assertNotEqual(result.exit_code, 0)
            # Rich wraps long messages at the console width, so ignore line breaks
            self.assertIn("does not look like a study", " ".join(result.output.split()))
            self.assertTrue((Path("mydata") / "important.txt").exists())

    def test_force_refuses_the_current_directory(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            args = self._project()
            # Even if it looks like a study, the current directory is never deleted
            (Path("build")).write_text("")
            (Path("run")).write_text("")

            result = self.runner.invoke(cli, args + ["--output", ".", "--force"])

            self.assertNotEqual(result.exit_code, 0)
            self.assertTrue((Path("proj") / "workflow.graphml").exists())

    def test_force_refuses_a_directory_containing_the_sources(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            args = self._project()
            (Path("proj") / "build").write_text("")
            (Path("proj") / "run").write_text("")

            result = self.runner.invoke(cli, args + ["--output", "proj", "--force"])

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("contains", result.output)
            self.assertTrue((Path("proj") / "workflow.graphml").exists())

    def test_force_refuses_a_regular_file(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            args = self._project()
            Path("out").write_text("not a directory")

            result = self.runner.invoke(cli, args + ["--output", "out", "--force"])

            self.assertNotEqual(result.exit_code, 0)
            self.assertEqual(Path("out").read_text(), "not a directory")


if __name__ == "__main__":
    unittest.main()
