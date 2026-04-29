#!/usr/bin/env python3
"""Deterministic fake video adapter for Plotloom contract tests."""
from __future__ import annotations
import argparse, shutil, subprocess, sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--prompt-file')
    args = parser.parse_args()
    if args.prompt_file:
        prompt = Path(args.prompt_file).expanduser().resolve()
        if not prompt.exists() or not prompt.is_file():
            print(f'missing prompt file: {prompt}', file=sys.stderr)
            return 2
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parents[2]
    fixture = repo_root / 'examples' / 'fixtures' / 'fake-video.mp4'
    if fixture.exists():
        shutil.copy2(fixture, output)
    else:
        cmd = [
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x180:d=1',
            '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
            '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(output)
        ]
        result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            return result.returncode
    print(f'fake video: {output}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
