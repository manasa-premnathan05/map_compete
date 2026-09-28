import sys
sys.path.insert(0, '.')
# Test if we can parse just the class structure
with open('scraper.py', 'r') as f:
    content = f.read()

# Find the class definition and method structure
lines = content.split('\n')
in_class = False
class_indent = 0
for i, line in enumerate(lines):
    stripped = line.lstrip()
    if stripped.startswith('class '):
        in_class = True
        class_indent = len(line) - len(stripped)
        print(f'Line {i+1}: CLASS at indent {class_indent}')
    elif in_class and stripped.startswith('def '):
        indent = len(line) - len(stripped)
        expected = class_indent + 4
        status = 'OK' if indent == expected else 'MISMATCH'
        print(f'Line {i+1}: METHOD "{stripped[:40]}" at indent {indent} (expected {expected}) {status}')
    elif in_class and stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
        indent = len(line) - len(stripped)
        if indent < class_indent + 4:
            print(f'Line {i+1}: CODE at indent {indent} (less than method level) - {stripped[:60]}')