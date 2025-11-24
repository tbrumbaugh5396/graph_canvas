#!/usr/bin/env python3
"""
Script to fix import issues in all Python files.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import os
import re
import glob

def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    print(f"Fixing imports in: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Add import handling at the top if not already present
    if 'Handle imports for both module and direct execution' not in content:
        # Find the first import statement
        lines = content.split('\n')
        insert_index = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                insert_index = i
                break
        
        # Insert the import handling code
        import_handling = '''# Handle imports for both module and direct execution
import sys
import os

# Add the parent directory to the path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

'''
        
        lines.insert(insert_index, import_handling)
        content = '\n'.join(lines)
    
    # Replace common import patterns
    replacements = [
        # GUI imports
        (r'^import graph_canvas.presentation.desktop.gui\.(\w+) as m_\w+', r'import graph_canvas.presentation.desktop.gui.\1 as m_\1'),
        (r'^from graph_canvas.presentation.desktop.gui\.(\w+) import', r'from graph_canvas.presentation.desktop.gui.\1 import'),
        
        # Event handler imports
        (r'^import graph_canvas.presentation.desktop.event_handlers\.(\w+) as m_\w+', r'import graph_canvas.presentation.desktop.event_handlers.\1 as m_\1'),
        (r'^from graph_canvas.presentation.desktop.event_handlers\.(\w+) import', r'from graph_canvas.presentation.desktop.event_handlers.\1 import'),
        
        # Model imports
        (r'^import graph_canvas.presentation.desktop.models\.(\w+) as m_\w+', r'import graph_canvas.presentation.desktop.models.\1 as m_\1'),
        (r'^from graph_canvas.presentation.desktop.models\.(\w+) import', r'from graph_canvas.presentation.desktop.models.\1 import'),
        
        # Utils imports
        (r'^import graph_canvas.presentation.desktop.utils\.(\w+) as m_\w+', r'import graph_canvas.presentation.desktop.utils.\1 as m_\1'),
        (r'^from graph_canvas.presentation.desktop.utils\.(\w+) import', r'from graph_canvas.presentation.desktop.utils.\1 import'),
        
        # File IO imports
        (r'^from graph_canvas.presentation.desktop.file_io\.(\w+) import', r'from graph_canvas.presentation.desktop.file_io.\1 import'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Fixed imports in {file_path}")
        return True
    else:
        print(f"  - No changes needed in {file_path}")
        return False

def main():
    """Main function to fix all imports."""
    print("🔧 Fixing import issues in all Python files...")
    
    # Get all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and not file.startswith('fix_imports'):
                python_files.append(os.path.join(root, file))
    
    fixed_count = 0
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n✅ Fixed imports in {fixed_count} files")

if __name__ == "__main__":
    main()
