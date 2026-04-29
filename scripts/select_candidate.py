#!/usr/bin/env python3
"""Copy an accepted Plotloom candidate to selected.* with backup semantics."""
from __future__ import annotations
import argparse, shutil, sys
from datetime import datetime
from pathlib import Path


def unique_backup_path(selected: Path) -> Path:
    ts = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    base = selected.with_name(f'{selected.stem}-prev-{ts}{selected.suffix}')
    if not base.exists():
        return base
    for i in range(1, 1000):
        candidate = selected.with_name(f'{selected.stem}-prev-{ts}-{i}{selected.suffix}')
        if not candidate.exists():
            return candidate
    raise RuntimeError('could not create unique selected backup path')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--selected', required=True)
    args = parser.parse_args()
    candidate = Path(args.candidate).expanduser().resolve()
    selected = Path(args.selected).expanduser().resolve()
    if not candidate.exists() or not candidate.is_file():
        print(f'missing candidate: {candidate}', file=sys.stderr)
        return 2
    selected.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if selected.exists():
        backup = unique_backup_path(selected)
        shutil.copy2(selected, backup)
    shutil.copy2(candidate, selected)
    print(f'selected: {candidate} -> {selected}')
    if backup:
        print(f'backup: {backup}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
