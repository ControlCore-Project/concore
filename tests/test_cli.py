import unittest
import tempfile
import shutil
import os
from pathlib import Path
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
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('1.0.0', result.output)
    
    def test_help(self):
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Usage:', result.output)
        self.assertIn('Commands:', result.output)
    
    def test_init_command(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            self.assertEqual(result.exit_code, 0)
            
            project_path = Path('test-project')
            self.assertTrue(project_path.exists())
            self.assertTrue((project_path / 'workflow.graphml').exists())
            self.assertTrue((project_path / 'src').exists())
            self.assertTrue((project_path / 'README.md').exists())
            self.assertTrue((project_path / 'src' / 'script.py').exists())
    
    def test_init_existing_directory(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            Path('existing').mkdir()
            result = self.runner.invoke(cli, ['init', 'existing'])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('already exists', result.output)
    
    def test_validate_missing_file(self):
        result = self.runner.invoke(cli, ['validate', 'nonexistent.graphml'])
        self.assertNotEqual(result.exit_code, 0)
    
    def test_validate_valid_file(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            self.assertEqual(result.exit_code, 0)
            
            result = self.runner.invoke(cli, ['validate', 'test-project/workflow.graphml'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Validation passed', result.output)

    def test_validate_missing_node_file(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            self.assertEqual(result.exit_code, 0)

            missing_file = Path('test-project/src/script.py')
            if missing_file.exists():
                missing_file.unlink()

            result = self.runner.invoke(cli, ['validate', 'test-project/workflow.graphml'])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('Missing source file', result.output)
    
    def test_status_command(self):
        result = self.runner.invoke(cli, ['status'])
        self.assertEqual(result.exit_code, 0)
    
    def test_run_command_missing_source(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            result = self.runner.invoke(cli, ['run', 'test-project/workflow.graphml', '--source', 'nonexistent'])
            self.assertNotEqual(result.exit_code, 0)

    def test_run_command_from_project_dir(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            self.assertEqual(result.exit_code, 0)

            result = self.runner.invoke(cli, [
                'run',
                'test-project/workflow.graphml',
                '--source', 'test-project/src',
                '--output', 'out',
                '--type', 'posix'
            ])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(Path('out/src/concore.py').exists())

    def test_run_command_default_type(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            self.assertEqual(result.exit_code, 0)

            result = self.runner.invoke(cli, [
                'run',
                'test-project/workflow.graphml',
                '--source', 'test-project/src',
                '--output', 'out'
            ])
            self.assertEqual(result.exit_code, 0)
            if os.name == 'nt':
                self.assertTrue(Path('out/build.bat').exists())
            else:
                self.assertTrue(Path('out/build').exists())

    def test_run_command_subdir_source(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            self.assertEqual(result.exit_code, 0)

            subdir = Path('test-project/src/subdir')
            subdir.mkdir(parents=True, exist_ok=True)
            shutil.move('test-project/src/script.py', subdir / 'script.py')

            workflow_path = Path('test-project/workflow.graphml')
            content = workflow_path.read_text()
            content = content.replace('N1:script.py', 'N1:subdir/script.py')
            workflow_path.write_text(content)

            result = self.runner.invoke(cli, [
                'run',
                'test-project/workflow.graphml',
                '--source', 'test-project/src',
                '--output', 'out',
                '--type', 'posix'
            ])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(Path('out/src/subdir/script.py').exists())

    def test_run_command_existing_output(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            Path('output').mkdir()
            
            result = self.runner.invoke(cli, [
                'run', 
                'test-project/workflow.graphml',
                '--source', 'test-project/src',
                '--output', 'output'
            ])
            self.assertIn('already exists', result.output.lower())
    
    def test_inspect_command_basic(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            self.assertEqual(result.exit_code, 0)
            
            result = self.runner.invoke(cli, ['inspect', 'test-project/workflow.graphml'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Workflow Overview', result.output)
            self.assertIn('Nodes:', result.output)
            self.assertIn('Edges:', result.output)
    
    def test_inspect_missing_file(self):
        result = self.runner.invoke(cli, ['inspect', 'nonexistent.graphml'])
        self.assertNotEqual(result.exit_code, 0)
    
    def test_inspect_json_output(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            self.assertEqual(result.exit_code, 0)
            
            result = self.runner.invoke(cli, ['inspect', 'test-project/workflow.graphml', '--json'])
            self.assertEqual(result.exit_code, 0)
            
            import json
            output_data = json.loads(result.output)
            self.assertIn('workflow', output_data)
            self.assertIn('nodes', output_data)
            self.assertIn('edges', output_data)
            self.assertEqual(output_data['workflow'], 'workflow.graphml')
    
    def test_inspect_missing_source_file(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            self.assertEqual(result.exit_code, 0)
            
            Path('test-project/src/script.py').unlink()
            
            result = self.runner.invoke(cli, ['inspect', 'test-project/workflow.graphml', '--source', 'src'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Missing files', result.output)

if __name__ == '__main__':
    unittest.main()
