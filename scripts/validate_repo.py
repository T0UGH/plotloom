#!/usr/bin/env python3
"""Validate minimal Plotloom series repo contract."""
from __future__ import annotations
import argparse, sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--episode')
    parser.add_argument('--require-video-prompts', action='store_true')
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()
    missing = []
    for rel in ['series.md', 'characters.md', 'episodes']:
        if not (repo / rel).exists():
            missing.append(str(repo / rel))
    ep = args.episode
    if ep:
        ep_dir = repo / 'episodes' / ep
        if not ep_dir.exists():
            missing.append(str(ep_dir))
        if args.require_video_prompts and not (ep_dir / 'video-prompts.md').exists():
            missing.append(str(ep_dir / 'video-prompts.md'))
    elif args.require_video_prompts:
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
