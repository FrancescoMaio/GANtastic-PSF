#!/usr/bin/env python3
"""Check this delivery without importing scientific dependencies or running simulations."""
import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    errors = []
    sources = json.loads((ROOT / 'SOURCE_MANIFEST.json').read_text())
    for name, expected in sources.items():
        path = ROOT / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f'Original source missing or modified: {name}')
    scripts = list(ROOT.rglob('*.py'))
    for path in scripts:
        try:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except SyntaxError as error:
            errors.append(str(error))
    docs = list(ROOT.rglob('*.md'))
    links = 0
    for path in docs:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if '://' in target or target.startswith('#'):
                continue
            links += 1
            target = target.split('#', 1)[0]
            if not (path.parent / target).exists():
                errors.append(f'Broken local link: {path.relative_to(ROOT)} -> {target}')
    if errors:
        print('\n'.join(errors))
        return 1
    print(f'PASS: {len(sources)} original hashes; {len(scripts)} Python syntax checks; {links} local links in {len(docs)} documents.')
    print('No imports of scientific modules; no simulation or training was executed.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
