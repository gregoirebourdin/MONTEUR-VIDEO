#!/usr/bin/env bash
# Final files for Instagram / YouTube Shorts from a rendered reel:
#   deliverables/<reel>/<reel>.mp4          picture + mix (voice, music, SFX)
#   deliverables/<reel>/<reel>_nomusic.mp4  same picture, voice + SFX only (add a trending sound in-app)
# The no-music version is a remux: never re-render for it.
# Usage: scripts/deliver.sh reel1 renders/reel1_v1.mp4
set -euo pipefail
cd "$(dirname "$0")/.."
id="$1"; src="$id/$2"; out="deliverables/$id"
mkdir -p "$out"
ffmpeg -v error -y -i "$src" -i "$id/audio/mix.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 \
  -movflags +faststart -shortest "$out/$id.mp4"
ffmpeg -v error -y -i "$src" -i "$id/audio/mix_nomusic.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 \
  -movflags +faststart -shortest "$out/${id}_nomusic.mp4"
for f in "$out/$id.mp4" "$out/${id}_nomusic.mp4"; do
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  lufs=$(ffmpeg -hide_banner -i "$f" -af ebur128=peak=true -f null - 2>&1 | grep -A20 Summary | grep -E "I:|Peak:" | tr -s ' ' | tr '\n' ' ')
  echo "$f  ${dur}s  $lufs"
done
