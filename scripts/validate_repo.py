#!/usr/bin/env python3
"""Validate minimal Plotloom series repo contract."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plotloom.repo import validate_repo


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--episode')
    parser.add_argument('--require-video-prompts', action='store_true')
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()
    result = validate_repo(repo, episode=args.episode, require_prompts=args.require_video_prompts)
    missing = [str(path) for path in result.missing]
    if not args.episode and args.require_video_prompts:
        prompts = list((repo / 'episodes').glob('ep*/video-prompts.md')) if (repo / 'episodes').exists() else []
        if not prompts:
            missing.append(str(repo / 'episodes/epXXX/video-prompts.md'))
    if missing:
        print('missing required Plotloom contract paths:')
        for p in missing:
            print(f'- {p}')
        return 2
    print(f'ok: {repo}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
