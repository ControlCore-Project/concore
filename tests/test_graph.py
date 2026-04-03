import unittest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner
from concore_cli.cli import cli


class TestGraphValidation(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def create_graph_file(self, filename, content):
        filepath = Path(self.temp_dir) / filename
        with open(filepath, "w") as f:
            f.write(content)
        return str(filepath)

    def test_validate_corrupted_xml(self):
        content = '<graphml><node id="n0">'
        filepath = self.create_graph_file("corrupted.graphml", content)

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("Validation failed", result.output)
        self.assertIn("Invalid XML", result.output)

    def test_validate_empty_file(self):
        filepath = self.create_graph_file("empty.graphml", "")

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("Validation failed", result.output)
        self.assertIn("File is empty", result.output)

    def test_validate_missing_node_id(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node>
                    <data key="d0"><y:NodeLabel>n0:script.py</y:NodeLabel></data>
                </node>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("missing_id.graphml", content)
        result = self.runner.invoke(cli, ["validate", filepath])
        self.assertIn("Validation failed", result.output)
        self.assertIn("Node missing required 'id' attribute", result.output)

    def test_validate_missing_edgedefault(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0:script.py</y:NodeLabel></data>
                </node>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("missing_default.graphml", content)
        result = self.runner.invoke(cli, ["validate", filepath])
        self.assertIn("Validation failed", result.output)
        self.assertIn("Graph missing required 'edgedefault'", result.output)

    def test_validate_missing_root_element(self):
        content = '<?xml version="1.0"?><other_root></other_root>'
        filepath = self.create_graph_file("not_graphml.xml", content)

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("Validation failed", result.output)
        self.assertIn("missing <graphml> root element", result.output)

    def test_validate_broken_edges(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0:script.py</y:NodeLabel></data>
                </node>
                <edge source="n0" target="n1"/>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("bad_edge.graphml", content)

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("Validation failed", result.output)
        self.assertIn("Edge references non-existent target node", result.output)

    def test_validate_node_missing_filename(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0:</y:NodeLabel></data>
                </node>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("bad_node.graphml", content)

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("Validation failed", result.output)
        self.assertIn("has no filename", result.output)

    def test_validate_unsafe_node_label(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0;rm -rf /:script.py</y:NodeLabel></data>
                </node>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("injection.graphml", content)

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("Validation failed", result.output)
        self.assertIn("unsafe shell characters", result.output)

    def test_validate_valid_graph(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0:script.py</y:NodeLabel></data>
                </node>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("valid.graphml", content)

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("Validation passed", result.output)
        self.assertIn("Workflow is valid", result.output)

    def test_validate_missing_source_file(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0:missing.py</y:NodeLabel></data>
                </node>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("workflow.graphml", content)
        source_dir = Path(self.temp_dir) / "src"
        source_dir.mkdir()

        result = self.runner.invoke(
            cli, ["validate", filepath, "--source", str(source_dir)]
        )

        self.assertIn("Validation failed", result.output)
        self.assertIn("Missing source file", result.output)

    def test_validate_with_existing_source_file(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0:exists.py</y:NodeLabel></data>
                </node>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("workflow.graphml", content)
        source_dir = Path(self.temp_dir) / "src"
        source_dir.mkdir()
        (source_dir / "exists.py").write_text('print("hello")')

        result = self.runner.invoke(
            cli, ["validate", filepath, "--source", str(source_dir)]
        )

        self.assertIn("Validation passed", result.output)

    def test_validate_zmq_port_conflict(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0:script1.py</y:NodeLabel></data>
                </node>
                <node id="n1">
                    <data key="d0"><y:NodeLabel>n1:script2.py</y:NodeLabel></data>
                </node>
                <edge source="n0" target="n1">
                    <data key="d1"><y:EdgeLabel>0x1234_portA</y:EdgeLabel></data>
                </edge>
                <edge source="n1" target="n0">
                    <data key="d1"><y:EdgeLabel>0x1234_portB</y:EdgeLabel></data>
                </edge>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("conflict.graphml", content)

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("Validation failed", result.output)
        self.assertIn("Port conflict", result.output)

    def test_validate_reserved_port(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0:script1.py</y:NodeLabel></data>
                </node>
                <node id="n1">
                    <data key="d0"><y:NodeLabel>n1:script2.py</y:NodeLabel></data>
                </node>
                <edge source="n0" target="n1">
                    <data key="d1"><y:EdgeLabel>0x50_data</y:EdgeLabel></data>
                </edge>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("reserved.graphml", content)

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("Port 80", result.output)
        self.assertIn("reserved range", result.output)

    def test_validate_cycle_detection(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0:controller.py</y:NodeLabel></data>
                </node>
                <node id="n1">
                    <data key="d0"><y:NodeLabel>n1:plant.py</y:NodeLabel></data>
                </node>
                <edge source="n0" target="n1">
                    <data key="d1"><y:EdgeLabel>control_signal</y:EdgeLabel></data>
                </edge>
                <edge source="n1" target="n0">
                    <data key="d1"><y:EdgeLabel>sensor_data</y:EdgeLabel></data>
                </edge>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("cycle.graphml", content)

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("cycles", result.output)
        self.assertIn("control loops", result.output)

    def test_validate_port_zero(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0:script1.py</y:NodeLabel></data>
                </node>
                <node id="n1">
                    <data key="d0"><y:NodeLabel>n1:script2.py</y:NodeLabel></data>
                </node>
                <edge source="n0" target="n1">
                    <data key="d1"><y:EdgeLabel>0x0_invalid</y:EdgeLabel></data>
                </edge>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("port_zero.graphml", content)

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("Validation failed", result.output)
        self.assertIn("must be at least 1", result.output)

    def test_validate_port_exceeds_maximum(self):
        content = """
        <graphml xmlns:y="http://www.yworks.com/xml/graphml">
            <graph id="G" edgedefault="directed">
                <node id="n0">
                    <data key="d0"><y:NodeLabel>n0:script1.py</y:NodeLabel></data>
                </node>
                <node id="n1">
                    <data key="d0"><y:NodeLabel>n1:script2.py</y:NodeLabel></data>
                </node>
                <edge source="n0" target="n1">
                    <data key="d1"><y:EdgeLabel>0x10000_toobig</y:EdgeLabel></data>
                </edge>
            </graph>
        </graphml>
        """
        filepath = self.create_graph_file("port_max.graphml", content)

        result = self.runner.invoke(cli, ["validate", filepath])

        self.assertIn("Validation failed", result.output)
        self.assertIn("exceeds maximum (65535)", result.output)


if __name__ == "__main__":
    unittest.main()
