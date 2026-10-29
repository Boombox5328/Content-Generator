#!/usr/bin/env bash
# Builds out/what_if_aliens.mp4  (needs: python3, numpy, pillow, ffmpeg; no speech / TTS)
set -euo pipefail
cd "$(dirname "$0")"
WORK=${TMPDIR:-/tmp}/alien_war_work
mkdir -p ../out "$WORK"
python3 audio.py "$WORK/audio.wav"
python3 render.py ../out/what_if_aliens.mp4 "$WORK/audio.wav"
