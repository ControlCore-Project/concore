import unittest
import tempfile
import shutil
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
    
    def test_status_command(self):
        result = self.runner.invoke(cli, ['status'])
        self.assertEqual(result.exit_code, 0)
    
    def test_run_command_missing_source(self):
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init', 'test-project'])
            result = self.runner.invoke(cli, ['run', 'test-project/workflow.graphml', '--source', 'nonexistent'])
            self.assertNotEqual(result.exit_code, 0)
    
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

if __name__ == '__main__':
    unittest.main()
