#!/usr/bin/env bash
# Builds out/the_long_way_out.mp4  (needs: python3, numpy, pillow, ffmpeg, espeak-ng, Inter font)
set -euo pipefail
cd "$(dirname "$0")"
WORK=${TMPDIR:-/tmp}/long_way_out_work
mkdir -p ../out "$WORK"
python3 audio.py "$WORK/audio.wav" "$WORK/vo"
python3 render.py ../out/the_long_way_out.mp4 "$WORK/audio.wav"
