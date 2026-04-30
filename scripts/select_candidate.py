#!/usr/bin/env python3
"""Copy an accepted Plotloom candidate to selected.* with backup semantics."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from plotloom.paths import selected_for_candidate
from plotloom.selection import select_candidate, unique_backup_path


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
    try:
        default_selected = selected_for_candidate(candidate)
    except ValueError:
        default_selected = None
    if default_selected is not None and default_selected == selected:
        result = select_candidate(candidate)
        print(f'selected: {candidate} -> {result.selected_path}')
        if result.backup_path:
            print(f'backup: {result.backup_path}')
        return 0
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
