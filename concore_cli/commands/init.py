import os
import shutil
from pathlib import Path
from rich.panel import Panel

SAMPLE_GRAPHML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd" xmlns:y="http://www.yworks.com/xml/graphml">
  <key for="node" id="d6" yfiles.type="nodegraphics"/>
  <key for="edge" id="d10" yfiles.type="edgegraphics"/>
  <graph edgedefault="directed" id="1" projectName="sample">
    <node id="n1">
      <data key="d6">
        <y:ShapeNode>
          <y:Geometry height="50" width="150" x="100" y="100"/>
          <y:Fill color="#ffcc00" opacity="1"/>
          <y:BorderStyle color="#000" width="1"/>
          <y:NodeLabel>N1:script.py</y:NodeLabel>
          <y:Shape type="rectangle"/>
        </y:ShapeNode>
      </data>
    </node>
  </graph>
</graphml>
'''

SAMPLE_PYTHON = '''import concore

while not concore.concore_unchanged():
    data = concore.concore_read()
    result = data * 2
    concore.concore_write(result)
'''

README_TEMPLATE = '''# {project_name}

A concore workflow project.

## Getting Started

1. Edit your workflow in `workflow.graphml` using yEd or similar GraphML editor
2. Add your processing scripts to the `src/` directory
3. Run your workflow:
   ```
   concore run workflow.graphml
   ```

## Project Structure

- `workflow.graphml` - Your workflow definition
- `src/` - Source files for your nodes
- `README.md` - This file

## Next Steps

- Modify `workflow.graphml` to define your processing pipeline
- Add Python/C++/MATLAB scripts to `src/`
- Use `concore validate workflow.graphml` to check your workflow
- Use `concore status` to monitor running processes
'''

def init_project(name, template, console):
    project_path = Path(name)
    
    if project_path.exists():
        raise FileExistsError(f"Directory '{name}' already exists")
    
    console.print(f"[cyan]Creating project:[/cyan] {name}")
    
    project_path.mkdir()
    (project_path / 'src').mkdir()
    
    workflow_file = project_path / 'workflow.graphml'
    with open(workflow_file, 'w') as f:
        f.write(SAMPLE_GRAPHML)
    
    sample_script = project_path / 'src' / 'script.py'
    with open(sample_script, 'w') as f:
        f.write(SAMPLE_PYTHON)
    
    readme_file = project_path / 'README.md'
    with open(readme_file, 'w') as f:
        f.write(README_TEMPLATE.format(project_name=name))
    
    console.print()
    console.print(Panel.fit(
        f"[green]✓[/green] Project created successfully!\n\n"
        f"Next steps:\n"
        f"  cd {name}\n"
        f"  concore validate workflow.graphml\n"
        f"  concore run workflow.graphml",
        title="Success",
        border_style="green"
    ))
