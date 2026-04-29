#!/usr/bin/env python3
"""Probe media with ffprobe and print concise JSON."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('video')
    args = parser.parse_args()
    video = Path(args.video).expanduser().resolve()
    if not video.exists():
        print(f'missing video: {video}', file=sys.stderr)
        return 2
    cmd = ['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', str(video)]
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return result.returncode
    data = json.loads(result.stdout or '{}')
    print(json.dumps({
        'path': str(video),
        'streams': len(data.get('streams', [])),
        'duration': data.get('format', {}).get('duration'),
        'format_name': data.get('format', {}).get('format_name'),
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
