#!/usr/bin/env python3
"""Initialize a Plotloom series repo from templates/series-repo."""
from __future__ import annotations
import argparse, re, shutil, sys
from pathlib import Path

TEXT_EXTS = {'.md', '.toml', '.txt'}
SAFE_SLUG = re.compile(r'^[a-z0-9][a-z0-9-]*$')


def toml_str(value: object) -> str:
    """Serialize a string as a minimal valid TOML basic string."""
    s = str(value)
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r') + '"'


def copy_template(src: Path, dst: Path, slug: str, title: str) -> None:
    for item in src.rglob('*'):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if item.suffix in TEXT_EXTS:
            text = item.read_text(encoding='utf-8')
            text = text.replace('{{slug}}', slug).replace('{{title}}', title)
            target.write_text(text, encoding='utf-8')
        else:
            shutil.copy2(item, target)


def update_home_registry(slug: str, title: str, path: Path) -> None:
    registry = Path.home() / 'plotloom.toml'
    entry = '\n'.join([
        '[[repos]]',
        f'slug = {toml_str(slug)}',
        f'title = {toml_str(title)}',
        f'path = {toml_str(path)}',
        'status = "active"',
        '',
    ])
    if registry.exists():
        text = registry.read_text(encoding='utf-8')
        if f'slug = {toml_str(slug)}' in text or f'path = {toml_str(path)}' in text:
            print(f'registry already contains slug/path: {registry}')
            return
        if text and not text.endswith('\n'):
            text += '\n'
        registry.write_text(text + '\n' + entry, encoding='utf-8')
    else:
        registry.write_text('# Plotloom home repo registry\n\n' + entry, encoding='utf-8')
    print(f'updated registry: {registry}')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--slug', required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--path', required=True)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    if not SAFE_SLUG.match(args.slug):
        print('invalid --slug; use lowercase letters, digits, and hyphens, starting with alnum', file=sys.stderr)
        return 2
    if '\n' in args.title or '\r' in args.title:
        print('invalid --title; newlines are not allowed', file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[1]
    template = repo_root / 'templates' / 'series-repo'
    target = Path(args.path).expanduser().resolve()
    if not template.exists():
        print(f'missing template: {template}', file=sys.stderr)
        return 2
    if target.exists() and any(target.iterdir()) and not args.force:
        print(f'target exists and is not empty: {target}', file=sys.stderr)
        return 3
    target.mkdir(parents=True, exist_ok=True)
    copy_template(template, target, args.slug, args.title)
    update_home_registry(args.slug, args.title, target)
    print(f'created series repo: {target}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
