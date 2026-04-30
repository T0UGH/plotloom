#!/usr/bin/env python3
"""Probe media with ffprobe and print concise JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plotloom.errors import MediaValidationError
from plotloom.media import probe_media


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('video')
    args = parser.parse_args()
    video = Path(args.video).expanduser().resolve()
    if not video.exists():
        print(f'missing video: {video}', file=sys.stderr)
        return 2
    try:
        facts = probe_media(video)
    except MediaValidationError as error:
        print(error.message, file=sys.stderr)
        return error.exit_code
    print(json.dumps(facts.to_dict(), ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
