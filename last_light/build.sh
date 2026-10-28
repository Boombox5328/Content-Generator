#!/usr/bin/env bash
# Builds out/the_last_light.mp4  (needs: python3, numpy, pillow, ffmpeg, espeak-ng)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p ../out /tmp/last_light_work
python3 audio.py /tmp/last_light_work/audio.wav /tmp/last_light_work/vo
python3 render.py ../out/the_last_light.mp4 /tmp/last_light_work/audio.wav
