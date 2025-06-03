#!/usr/bin/env python3
"""
Convert Jupyter notebook (.ipynb) to marimo notebook (.py) format.

Usage:
    python jupyter_to_marimo.py input.ipynb output.py
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Set


def sanitize_function_name(name: str) -> str:
    """Convert a string to a valid Python function name."""
    # Replace invalid characters with underscore
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # Ensure it starts with a letter or underscore
    if name and name[0].isdigit():
        name = f'_{name}'
    # Ensure it's not empty
    if not name:
        name = 'cell'
    return name


def extract_variables(code: str) -> Set[str]:
    """
    Extract variable names that are assigned in the code.
    This helps determine what should be returned from the cell.
    """
    import ast
    
    variables = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.add(target.id)
                    elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                variables.add(elt.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                variables.add(node.target.id)
            elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
                variables.add(node.target.id)
    except SyntaxError:
        pass
    
    return variables


def detect_imports(code: str) -> Set[str]:
    """Detect import statements and imported names."""
    import ast
    
    imports = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.add(name.split('.')[0])  # Get the top-level module
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    if name != '*':
                        imports.add(name)
    except SyntaxError:
        pass
    
    return imports


def determine_return_variables(code: str, cell_index: int) -> List[str]:
    """
    Determine what variables should be returned from a marimo cell.
    """
    variables = extract_variables(code)
    imports = detect_imports(code)
    
    # Filter out common temporary variables and imports
    filtered_vars = []
    temp_patterns = {'_', 'temp', 'tmp', 'i', 'j', 'k', 'idx', 'index'}
    
    for var in variables:
        if (var not in imports and 
            var not in temp_patterns and 
            not var.startswith('_') and
            not var.isupper()):  # Skip constants
            filtered_vars.append(var)
    
    # Sort for consistency
    return sorted(filtered_vars)


def process_code_cell(source: List[str], cell_index: int) -> str:
    """
    Convert a Jupyter code cell to a marimo cell function.
    """
    # Join source lines
    code = '\n'.join(source).strip()
    
    if not code:
        return ""
    
    # Generate function name
    func_name = f"cell_{cell_index + 1}"
    
    # Determine return variables
    return_vars = determine_return_variables(code, cell_index)
    
    # Create the marimo cell
    lines = ["@app.cell"]
    lines.append(f"def {func_name}():")
    
    # Indent the code
    for line in code.split('\n'):
        if line.strip():
            lines.append(f"    {line}")
        else:
            lines.append("")
    
    # Add return statement if there are variables to return
    if return_vars:
        if len(return_vars) == 1:
            lines.append(f"    return {return_vars[0]}")
        else:
            vars_str = ', '.join(return_vars)
            lines.append(f"    return {vars_str}")
    else:
        lines.append("    return")
    
    return '\n'.join(lines)


def process_markdown_cell(source: List[str]) -> str:
    """
    Convert a Jupyter markdown cell to a marimo markdown cell.
    """
    # Join source lines
    content = ''.join(source).strip()
    
    if not content:
        return ""
    
    # Escape triple quotes in the content
    content = content.replace('"""', '\\"\\"\\"')
    
    lines = ["@app.cell"]
    lines.append("def markdown_cell():")
    lines.append("    mo.md(")
    lines.append("        r\"\"\"")
    
    # Add markdown content with proper indentation
    for line in content.split('\n'):
        lines.append(f"        {line}")
    
    lines.append("        \"\"\"")
    lines.append("    )")
    lines.append("    return")
    
    return '\n'.join(lines)


def convert_jupyter_to_marimo(input_path: str, output_path: str) -> None:
    """
    Convert a Jupyter notebook to marimo format.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        print(f"Error: Input file '{input_path}' not found.")
        return
    
    # Read the Jupyter notebook
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    # Validate notebook format
    if 'cells' not in notebook:
        print("Error: Invalid Jupyter notebook format (no 'cells' key found).")
        return
    
    # Generate marimo code
    marimo_lines = []
    
    # Add marimo imports and app initialization
    marimo_lines.extend([
        "import marimo",
        "",
        "__generated_with = \"0.8.0\"",
        "app = marimo.App(width=\"medium\")",
        "",
    ])
    
    # Track if we need to import mo for markdown cells
    has_markdown = any(cell.get('cell_type') == 'markdown' for cell in notebook['cells'])
    if has_markdown:
        marimo_lines.extend([
            "@app.cell",
            "def imports():",
            "    import marimo as mo",
            "    return mo,",
            "",
        ])
    
    # Process each cell
    code_cell_count = 0
    for i, cell in enumerate(notebook['cells']):
        cell_type = cell.get('cell_type', 'code')
        source = cell.get('source', [])
        
        if cell_type == 'code':
            code_cell_count += 1
            cell_content = process_code_cell(source, code_cell_count - 1)
            if cell_content:
                marimo_lines.append(cell_content)
                marimo_lines.append("")
        
        elif cell_type == 'markdown':
            cell_content = process_markdown_cell(source)
            if cell_content:
                marimo_lines.append(cell_content)
                marimo_lines.append("")
    
    # Add the main execution block
    marimo_lines.extend([
        "",
        "if __name__ == \"__main__\":",
        "    app.run()"
    ])
    
    # Write the marimo notebook
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(marimo_lines))
        print(f"Successfully converted '{input_path}' to '{output_path}'")
        print(f"Processed {len(notebook['cells'])} cells ({code_cell_count} code cells).")
        
        if has_markdown:
            print("Note: Markdown cells converted to mo.md() calls.")
    except Exception as e:
        print(f"Error writing output file: {e}")


def analyze_notebook(input_path: str) -> None:
    """
    Analyze a Jupyter notebook and show conversion preview.
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        print(f"Error: Input file '{input_path}' not found.")
        return
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    if 'cells' not in notebook:
        print("Error: Invalid Jupyter notebook format.")
        return
    
    print(f"Jupyter Notebook Analysis: {input_path}")
    print("=" * 50)
    
    code_cells = 0
    markdown_cells = 0
    raw_cells = 0
    
    for i, cell in enumerate(notebook['cells']):
        cell_type = cell.get('cell_type', 'unknown')
        source_lines = len(cell.get('source', []))
        
        if cell_type == 'code':
            code_cells += 1
        elif cell_type == 'markdown':
            markdown_cells += 1
        elif cell_type == 'raw':
            raw_cells += 1
        
        print(f"Cell {i+1}: {cell_type} ({source_lines} lines)")
    
    print(f"\nSummary:")
    print(f"- Code cells: {code_cells}")
    print(f"- Markdown cells: {markdown_cells}")
    print(f"- Raw cells: {raw_cells}")
    print(f"- Total cells: {len(notebook['cells'])}")


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python jupyter_to_marimo.py <input.ipynb> <output.py>  # Convert notebook")
        print("  python jupyter_to_marimo.py --analyze <input.ipynb>    # Analyze notebook")
        print("\nExamples:")
        print("  python jupyter_to_marimo.py my_notebook.ipynb my_notebook.py")
        print("  python jupyter_to_marimo.py --analyze my_notebook.ipynb")
        sys.exit(1)
    
    if sys.argv[1] == "--analyze":
        if len(sys.argv) != 3:
            print("Usage: python jupyter_to_marimo.py --analyze <input.ipynb>")
            sys.exit(1)
        analyze_notebook(sys.argv[2])
    else:
        if len(sys.argv) != 3:
            print("Usage: python jupyter_to_marimo.py <input.ipynb> <output.py>")
            sys.exit(1)
        
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        
        convert_jupyter_to_marimo(input_path, output_path)


if __name__ == "__main__":
    main()
