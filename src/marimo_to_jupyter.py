#!/usr/bin/env python3
"""
Convert marimo notebook (.py) to Jupyter notebook (.ipynb) format.

Usage:
    python marimo_to_jupyter.py input.py output.ipynb
"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any


def parse_marimo_notebook(content: str) -> List[Dict[str, Any]]:
    """
    Parse a marimo notebook and extract cells.
    
    Marimo notebooks use @app.cell decorators to define cells.
    """
    cells = []
    
    # Parse the Python AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Error parsing Python file: {e}")
        return cells
    
    # Find all function definitions with @app.cell decorator
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if function has @app.cell decorator
            has_app_cell = any(
                (isinstance(decorator, ast.Attribute) and 
                 isinstance(decorator.value, ast.Name) and
                 decorator.value.id == 'app' and 
                 decorator.attr == 'cell') or
                (isinstance(decorator, ast.Call) and
                 isinstance(decorator.func, ast.Attribute) and
                 isinstance(decorator.func.value, ast.Name) and
                 decorator.func.value.id == 'app' and
                 decorator.func.attr == 'cell')
                for decorator in node.decorator_list
            )
            
            if has_app_cell:
                # Extract the function body
                cell_source = ast.get_source_segment(content, node)
                if cell_source:
                    # Remove the function definition wrapper and decorator
                    lines = cell_source.split('\n')
                    
                    # Find the start of the function body (after def line)
                    body_start = 0
                    for i, line in enumerate(lines):
                        if line.strip().startswith('def '):
                            body_start = i + 1
                            break
                    
                    # Extract function body and remove indentation
                    body_lines = lines[body_start:]
                    if body_lines:
                        # Remove common indentation
                        min_indent = float('inf')
                        for line in body_lines:
                            if line.strip():  # Skip empty lines
                                indent = len(line) - len(line.lstrip())
                                min_indent = min(min_indent, indent)
                        
                        if min_indent == float('inf'):
                            min_indent = 0
                        
                        # Remove the common indentation
                        cleaned_lines = []
                        for line in body_lines:
                            if line.strip():
                                cleaned_lines.append(line[min_indent:])
                            else:
                                cleaned_lines.append('')
                        
                        cell_content = '\n'.join(cleaned_lines).strip()
                        
                        # Remove return statement if it's the last line
                        lines = cell_content.split('\n')
                        if lines and lines[-1].strip().startswith('return '):
                            lines[-1] = lines[-1].replace('return ', '', 1)
                            cell_content = '\n'.join(lines)
                        
                        cells.append({
                            'cell_type': 'code',
                            'source': cell_content,
                            'metadata': {},
                            'execution_count': None,
                            'outputs': []
                        })
    
    # If no cells found with decorators, try to split by function definitions
    if not cells:
        cells = fallback_parse(content)
    
    return cells


def fallback_parse(content: str) -> List[Dict[str, Any]]:
    """
    Fallback parser for marimo files that don't use standard decorators.
    Split by function definitions or other patterns.
    """
    cells = []
    
    # Split by function definitions
    functions = re.split(r'\n(?=def\s+\w+)', content)
    
    for func in functions:
        func = func.strip()
        if func:
            # Skip imports and module-level code in the first section
            if not func.startswith('def '):
                # This might be imports or module-level code
                if any(line.strip().startswith(('import ', 'from ')) for line in func.split('\n')):
                    cell_type = 'code'
                else:
                    cell_type = 'code'
            else:
                cell_type = 'code'
            
            cells.append({
                'cell_type': cell_type,
                'source': func,
                'metadata': {},
                'execution_count': None,
                'outputs': []
            })
    
    return cells


def create_jupyter_notebook(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a Jupyter notebook structure from parsed cells.
    """
    notebook = {
        'cells': [],
        'metadata': {
            'kernelspec': {
                'display_name': 'Python 3',
                'language': 'python',
                'name': 'python3'
            },
            'language_info': {
                'name': 'python',
                'version': '3.8.0',
                'mimetype': 'text/x-python',
                'codemirror_mode': {
                    'name': 'ipython',
                    'version': 3
                },
                'pygments_lexer': 'ipython3',
                'nbconvert_exporter': 'python',
                'file_extension': '.py'
            }
        },
        'nbformat': 4,
        'nbformat_minor': 4
    }
    
    for cell in cells:
        jupyter_cell = {
            'cell_type': cell['cell_type'],
            'metadata': cell['metadata'],
            'source': cell['source'].split('\n') if cell['source'] else ['']
        }
        
        if cell['cell_type'] == 'code':
            jupyter_cell['execution_count'] = cell['execution_count']
            jupyter_cell['outputs'] = cell['outputs']
        
        notebook['cells'].append(jupyter_cell)
    
    return notebook


def convert_marimo_to_jupyter(input_path: str, output_path: str) -> None:
    """
    Convert a marimo notebook to Jupyter format.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        print(f"Error: Input file '{input_path}' not found.")
        return
    
    # Read the marimo notebook
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    # Parse the marimo notebook
    cells = parse_marimo_notebook(content)
    
    if not cells:
        print("Warning: No cells found in the marimo notebook.")
        # Create a single cell with the entire content
        cells = [{
            'cell_type': 'code',
            'source': content,
            'metadata': {},
            'execution_count': None,
            'outputs': []
        }]
    
    # Create Jupyter notebook structure
    notebook = create_jupyter_notebook(cells)
    
    # Write the Jupyter notebook
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=2, ensure_ascii=False)
        print(f"Successfully converted '{input_path}' to '{output_path}'")
        print(f"Created {len(cells)} cells in the Jupyter notebook.")
    except Exception as e:
        print(f"Error writing output file: {e}")


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 3:
        print("Usage: python marimo_to_jupyter.py <input.py> <output.ipynb>")
        print("\nExample:")
        print("  python marimo_to_jupyter.py my_notebook.py my_notebook.ipynb")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    convert_marimo_to_jupyter(input_path, output_path)


if __name__ == "__main__":
    main()
