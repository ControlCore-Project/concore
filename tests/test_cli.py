import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner
from concore_cli.cli import cli


class TestConcoreCLI(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_version(self):
        result = self.runner.invoke(cli, ["--version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("1.0.0", result.output)

    def test_help(self):
        result = self.runner.invoke(cli, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Usage:", result.output)
        self.assertIn("Commands:", result.output)

    def test_init_command(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            project_path = Path("test-project")
            self.assertTrue(project_path.exists())
            self.assertTrue((project_path / "workflow.graphml").exists())
            self.assertTrue((project_path / "src").exists())
            self.assertTrue((project_path / "README.md").exists())
            self.assertTrue((project_path / "src" / "script.py").exists())
            self.assertTrue((project_path / "STUDY.json").exists())

            metadata = json.loads((project_path / "STUDY.json").read_text())
            self.assertEqual(metadata["generated_by"], "concore init")
            self.assertEqual(metadata["study_name"], "test-project")
            self.assertEqual(metadata["schema_version"], 1)
            self.assertIn("workflow.graphml", metadata["checksums"])

    def test_init_existing_directory(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            Path("existing").mkdir()
            result = self.runner.invoke(cli, ["init", "existing"])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("already exists", result.output)

    def test_validate_missing_file(self):
        result = self.runner.invoke(cli, ["validate", "nonexistent.graphml"])
        self.assertNotEqual(result.exit_code, 0)

    def test_validate_valid_file(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            result = self.runner.invoke(
                cli, ["validate", "test-project/workflow.graphml"]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Validation passed", result.output)

    def test_validate_missing_node_file(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            missing_file = Path("test-project/src/script.py")
            if missing_file.exists():
                missing_file.unlink()

            result = self.runner.invoke(
                cli, ["validate", "test-project/workflow.graphml"]
            )
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("Missing source file", result.output)

    def test_validate_json_output_for_valid_file(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            result = self.runner.invoke(
                cli,
                ["validate", "test-project/workflow.graphml", "--format", "json"],
            )
            self.assertEqual(result.exit_code, 0)

            payload = json.loads(result.output)
            self.assertTrue(payload["valid"])
            self.assertEqual(payload["summary"]["error_count"], 0)
            self.assertEqual(payload["workflow"], "workflow.graphml")
            self.assertIn("src", payload["source_dir"])

    def test_validate_json_output_for_missing_source_file(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            missing_file = Path("test-project/src/script.py")
            if missing_file.exists():
                missing_file.unlink()

            result = self.runner.invoke(
                cli,
                ["validate", "test-project/workflow.graphml", "--format", "json"],
            )
            self.assertNotEqual(result.exit_code, 0)

            payload = json.loads(result.output)
            self.assertFalse(payload["valid"])
            self.assertEqual(payload["summary"]["error_count"], 1)
            self.assertEqual(payload["errors"][0]["error_type"], "missing_source_file")
            self.assertEqual(payload["errors"][0]["node_id"], "n1")

    def test_status_command(self):
        result = self.runner.invoke(cli, ["status"])
        self.assertEqual(result.exit_code, 0)

    def test_build_command_missing_source(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            result = self.runner.invoke(
                cli,
                ["build", "test-project/workflow.graphml", "--source", "nonexistent"],
            )
            self.assertNotEqual(result.exit_code, 0)

    def test_build_command_from_project_dir(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            result = self.runner.invoke(
                cli,
                [
                    "build",
                    "test-project/workflow.graphml",
                    "--source",
                    "test-project/src",
                    "--output",
                    "out",
                    "--type",
                    "posix",
                ],
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(Path("out/src/concore.py").exists())
            self.assertTrue(Path("out/STUDY.json").exists())

            metadata = json.loads(Path("out/STUDY.json").read_text())
            self.assertEqual(metadata["generated_by"], "concore build")
            self.assertEqual(metadata["study_name"], "out")
            self.assertEqual(metadata["schema_version"], 1)
            self.assertIn("workflow.graphml", metadata["checksums"])

    def test_build_command_default_type(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            result = self.runner.invoke(
                cli,
                [
                    "build",
                    "test-project/workflow.graphml",
                    "--source",
                    "test-project/src",
                    "--output",
                    "out",
                ],
            )
            self.assertEqual(result.exit_code, 0)
            if os.name == "nt":
                self.assertTrue(Path("out/build.bat").exists())
            else:
                self.assertTrue(Path("out/build").exists())

    def test_build_command_quotes_posix_tool_path_with_spaces(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            with patch.dict(
                os.environ,
                {"CONCORE_PYTHONEXE": "/opt/custom tools/python3"},
                clear=False,
            ):
                result = self.runner.invoke(
                    cli,
                    [
                        "build",
                        "test-project/workflow.graphml",
                        "--source",
                        "test-project/src",
                        "--output",
                        "out",
                        "--type",
                        "posix",
                    ],
                )

            self.assertEqual(result.exit_code, 0)
            run_script = Path("out/run").read_text()
            self.assertIn("'/opt/custom tools/python3' script.py", run_script)

    def test_build_command_quotes_windows_tool_path_with_spaces(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            with patch.dict(
                os.environ,
                {"CONCORE_PYTHONWIN": r"C:\Program Files\Python313\python.exe"},
                clear=False,
            ):
                result = self.runner.invoke(
                    cli,
                    [
                        "build",
                        "test-project/workflow.graphml",
                        "--source",
                        "test-project/src",
                        "--output",
                        "out",
                        "--type",
                        "windows",
                    ],
                )

            self.assertEqual(result.exit_code, 0)
            run_script = Path("out/run.bat").read_text()
            self.assertIn(
                '"C:\\Program Files\\Python313\\python.exe" "script.py"',
                run_script,
            )

    def test_build_command_nested_output_path(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            result = self.runner.invoke(
                cli,
                [
                    "build",
                    "test-project/workflow.graphml",
                    "--source",
                    "test-project/src",
                    "--output",
                    "build/out",
                    "--type",
                    "posix",
                ],
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(Path("build/out/src/concore.py").exists())

    def test_build_command_subdir_source(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            subdir = Path("test-project/src/subdir")
            subdir.mkdir(parents=True, exist_ok=True)
            shutil.move("test-project/src/script.py", subdir / "script.py")

            workflow_path = Path("test-project/workflow.graphml")
            content = workflow_path.read_text()
            content = content.replace("N1:script.py", "N1:subdir/script.py")
            workflow_path.write_text(content)

            result = self.runner.invoke(
                cli,
                [
                    "build",
                    "test-project/workflow.graphml",
                    "--source",
                    "test-project/src",
                    "--output",
                    "out",
                    "--type",
                    "posix",
                ],
            )
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(Path("out/src/subdir/script.py").exists())

    def test_build_command_docker_subdir_source_build_paths(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            subdir = Path("test-project/src/subdir")
            subdir.mkdir(parents=True, exist_ok=True)
            shutil.move("test-project/src/script.py", subdir / "script.py")

            workflow_path = Path("test-project/workflow.graphml")
            content = workflow_path.read_text()
            content = content.replace("N1:script.py", "N1:subdir/script.py")
            workflow_path.write_text(content)

            result = self.runner.invoke(
                cli,
                [
                    "build",
                    "test-project/workflow.graphml",
                    "--source",
                    "test-project/src",
                    "--output",
                    "out",
                    "--type",
                    "docker",
                ],
            )
            self.assertEqual(result.exit_code, 0)

            build_script = Path("out/build").read_text()
            self.assertIn("mkdir docker-subdir__script", build_script)
            self.assertIn("cp ../src/Dockerfile.subdir/script Dockerfile", build_script)
            self.assertIn("cp ../src/subdir/script.py .", build_script)
            self.assertIn("cp ../src/subdir/script.iport concore.iport", build_script)
            self.assertIn("cd ..", build_script)

    def test_build_command_compose_requires_docker_type(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            result = self.runner.invoke(
                cli,
                [
                    "build",
                    "test-project/workflow.graphml",
                    "--source",
                    "test-project/src",
                    "--output",
                    "out",
                    "--type",
                    "posix",
                    "--compose",
                ],
            )
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn(
                "--compose can only be used with --type docker", result.output
            )

    def test_build_command_docker_compose_single_node(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            result = self.runner.invoke(
                cli,
                [
                    "build",
                    "test-project/workflow.graphml",
                    "--source",
                    "test-project/src",
                    "--output",
                    "out",
                    "--type",
                    "docker",
                    "--compose",
                ],
            )
            self.assertEqual(result.exit_code, 0)

            compose_path = Path("out/docker-compose.yml")
            self.assertTrue(compose_path.exists())
            compose_content = compose_path.read_text()
            self.assertIn("services:", compose_content)
            self.assertIn("container_name: 'N1'", compose_content)
            self.assertIn("image: 'docker-script'", compose_content)
            self.assertIn("networks:", compose_content)
            self.assertIn("concore_net:", compose_content)
            self.assertIn("- concore_net", compose_content)
            self.assertIn("restart: on-failure", compose_content)

            metadata = json.loads(Path("out/STUDY.json").read_text())
            self.assertIn("docker-compose.yml", metadata["checksums"])

    def test_build_command_docker_compose_multi_node(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            Path("src").mkdir()
            Path("src/common.py").write_text(
                "import concore\n\ndef step():\n    return None\n"
            )

            workflow = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd" xmlns:y="http://www.yworks.com/xml/graphml">
  <key for="node" id="d6" yfiles.type="nodegraphics"/>
  <key for="edge" id="d10" yfiles.type="edgegraphics"/>
  <graph edgedefault="directed" id="G">
        <node id="n1"><data key="d6"><y:ShapeNode><y:NodeLabel>A:common.py</y:NodeLabel></y:ShapeNode></data></node>
        <node id="n2"><data key="d6"><y:ShapeNode><y:NodeLabel>B:common.py</y:NodeLabel></y:ShapeNode></data></node>
        <node id="n3"><data key="d6"><y:ShapeNode><y:NodeLabel>C:common.py</y:NodeLabel></y:ShapeNode></data></node>
        <edge source="n1" target="n2"><data key="d10"><y:PolyLineEdge><y:EdgeLabel>0x1000_AB</y:EdgeLabel></y:PolyLineEdge></data></edge>
        <edge source="n2" target="n3"><data key="d10"><y:PolyLineEdge><y:EdgeLabel>0x1001_BC</y:EdgeLabel></y:PolyLineEdge></data></edge>
  </graph>
</graphml>
"""
            Path("workflow.graphml").write_text(workflow)

            result = self.runner.invoke(
                cli,
                [
                    "build",
                    "workflow.graphml",
                    "--source",
                    "src",
                    "--output",
                    "out",
                    "--type",
                    "docker",
                    "--compose",
                ],
            )
            self.assertEqual(result.exit_code, 0)

            compose_content = Path("out/docker-compose.yml").read_text()
            self.assertIn("container_name: 'A'", compose_content)
            self.assertIn("container_name: 'B'", compose_content)
            self.assertIn("container_name: 'C'", compose_content)
            self.assertIn("image: 'docker-common'", compose_content)

    def test_build_command_docker_requirements_injection(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            Path("requirements.txt").write_text("pandas==1.0.0")

            result = self.runner.invoke(
                cli,
                [
                    "build",
                    "test-project/workflow.graphml",
                    "--source",
                    "test-project/src",
                    "--output",
                    "out",
                    "--type",
                    "docker",
                ],
            )
            self.assertEqual(result.exit_code, 0)

            req_path = Path("out/src/requirements.txt")
            self.assertTrue(req_path.exists())
            self.assertEqual(req_path.read_text(), "pandas==1.0.0")

            build_script = Path("out/build").read_text()
            self.assertIn("cp ../src/requirements.txt .", build_script)

    def test_build_command_shared_source_specialization_merges_edge_params(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            Path("src").mkdir()
            Path("src/common.py").write_text(
                "import concore\n\ndef step():\n    return None\n"
            )

            workflow = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd" xmlns:y="http://www.yworks.com/xml/graphml">
  <key for="node" id="d6" yfiles.type="nodegraphics"/>
  <key for="edge" id="d10" yfiles.type="edgegraphics"/>
  <graph edgedefault="directed" id="G">
    <node id="n1"><data key="d6"><y:ShapeNode><y:NodeLabel>A:common.py</y:NodeLabel></y:ShapeNode></data></node>
    <node id="n2"><data key="d6"><y:ShapeNode><y:NodeLabel>B:common.py</y:NodeLabel></y:ShapeNode></data></node>
    <node id="n3"><data key="d6"><y:ShapeNode><y:NodeLabel>C:common.py</y:NodeLabel></y:ShapeNode></data></node>
    <edge source="n1" target="n2"><data key="d10"><y:PolyLineEdge><y:EdgeLabel>0x1000_AB</y:EdgeLabel></y:PolyLineEdge></data></edge>
    <edge source="n2" target="n3"><data key="d10"><y:PolyLineEdge><y:EdgeLabel>0x1001_BC</y:EdgeLabel></y:PolyLineEdge></data></edge>
  </graph>
</graphml>
"""
            Path("workflow.graphml").write_text(workflow)

            result = self.runner.invoke(
                cli,
                [
                    "build",
                    "workflow.graphml",
                    "--source",
                    "src",
                    "--output",
                    "out",
                    "--type",
                    "posix",
                ],
            )
            self.assertEqual(result.exit_code, 0)

            specialized_script = Path("out/src/common.py")
            self.assertTrue(specialized_script.exists())
            content = specialized_script.read_text()
            self.assertIn("PORT_NAME_A_B", content)
            self.assertIn("PORT_A_B", content)
            self.assertIn("PORT_NAME_B_C", content)
            self.assertIn("PORT_B_C", content)

    def test_build_command_existing_output(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            Path("output").mkdir()

            result = self.runner.invoke(
                cli,
                [
                    "build",
                    "test-project/workflow.graphml",
                    "--source",
                    "test-project/src",
                    "--output",
                    "output",
                ],
            )
            self.assertIn("already exists", result.output.lower())

    def test_inspect_command_basic(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            result = self.runner.invoke(
                cli, ["inspect", "test-project/workflow.graphml"]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Workflow Overview", result.output)
            self.assertIn("Nodes:", result.output)
            self.assertIn("Edges:", result.output)

    def test_inspect_missing_file(self):
        result = self.runner.invoke(cli, ["inspect", "nonexistent.graphml"])
        self.assertNotEqual(result.exit_code, 0)

    def test_inspect_json_output(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            result = self.runner.invoke(
                cli, ["inspect", "test-project/workflow.graphml", "--json"]
            )
            self.assertEqual(result.exit_code, 0)

            import json

            output_data = json.loads(result.output)
            self.assertIn("workflow", output_data)
            self.assertIn("nodes", output_data)
            self.assertIn("edges", output_data)
            self.assertEqual(output_data["workflow"], "workflow.graphml")

    def test_inspect_missing_source_file(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ["init", "test-project"])
            self.assertEqual(result.exit_code, 0)

            Path("test-project/src/script.py").unlink()

            result = self.runner.invoke(
                cli, ["inspect", "test-project/workflow.graphml", "--source", "src"]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Missing files", result.output)


if __name__ == "__main__":
    unittest.main()
