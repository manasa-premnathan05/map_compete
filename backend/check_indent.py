with open('scraper.py', 'rb') as f:
    content = f.read()
lines = content.split(b'\n')
for i in range(720, 760):
    line = lines[i]
    stripped = line.lstrip()
    if stripped.startswith(b'def '):
        spaces = len(line) - len(stripped)
        print(f'{i+1}: {spaces} | {line[:100]}')
    elif stripped and not stripped.startswith(b'#') and not stripped.startswith(b'"""'):
        spaces = len(line) - len(stripped)
        if spaces < 8:
            print(f'{i+1}: {spaces} | {line[:100]}')