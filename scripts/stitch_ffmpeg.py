#!/usr/bin/env python3
"""Stitch selected Plotloom clips into final.mp4 with ffmpeg."""
from __future__ import annotations
import argparse, subprocess, sys, tempfile
from pathlib import Path


def probe(path: Path) -> bool:
    return subprocess.run(['ffprobe', '-v', 'error', str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('clips', nargs='+')
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    clips = [Path(c).expanduser().resolve() for c in args.clips]
    missing = [str(c) for c in clips if not c.exists()]
    if missing:
        print('missing clips:', file=sys.stderr)
        print('\n'.join(missing), file=sys.stderr)
        return 2
    bad = [str(c) for c in clips if not probe(c)]
    if bad:
        print('unprobeable clips:', file=sys.stderr)
        print('\n'.join(bad), file=sys.stderr)
        return 3
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        norm = []
        for i, clip in enumerate(clips, 1):
            n = tmp / f'clip-{i:03d}.mp4'
            cmd = ['ffmpeg', '-y', '-i', str(clip), '-vf', 'scale=320:180,fps=24', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '44100', '-ac', '2', str(n)]
            r = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if r.returncode != 0:
                print(r.stderr, file=sys.stderr)
                return r.returncode
            norm.append(n)
        concat = tmp / 'concat.txt'
        concat.write_text(''.join(f"file '{p}'\n" for p in norm), encoding='utf-8')
        cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(output)]
        r = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            return r.returncode
    if not probe(output):
        print(f'final output is not probeable: {output}', file=sys.stderr)
        return 4
    print(f'final: {output}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
