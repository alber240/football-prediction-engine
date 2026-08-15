"""
Convert all Python files to LF line endings
"""

import os

def convert_to_lf(filepath):
    """Convert file from CRLF to LF"""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Remove all \r\n and replace with \n
        content = content.replace(b'\r\n', b'\n')
        # Also remove any stray \r
        content = content.replace(b'\r', b'\n')
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        print(f"✅ Fixed: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")
        return False

# Find all Python files
python_files = []
for root, dirs, files in os.walk('app'):
    for file in files:
        if file.endswith('.py'):
            python_files.append(os.path.join(root, file))

# Also fix test files
for f in ['test_simple.py', 'test_imports.py', 'fix_all_files.py']:
    if os.path.exists(f):
        python_files.append(f)

print(f"Found {len(python_files)} Python files to fix")

for f in python_files:
    convert_to_lf(f)

print("\n✅ All files converted to LF line endings!")