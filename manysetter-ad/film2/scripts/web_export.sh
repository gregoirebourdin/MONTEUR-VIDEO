#!/usr/bin/env bash
# Web delivery for the sales page: H.264 MP4 (every browser), VP9 WebM (lighter in Chrome/Firefox),
# poster frames. Usage: scripts/web_export.sh <mastered.mp4> <out_dir> <poster_time_s> [<poster2_time_s>]
set -euo pipefail
src="$1"; out="$2"; t1="$3"; t2="${4:-}"
mkdir -p "$out"

# H.264 High, 1080p60, progressive download starts playing at once (faststart)
ffmpeg -v error -y -i "$src" -c:v libx264 -preset slow -crf 23 -profile:v high -level 4.2 -pix_fmt yuv420p \
  -r 60 -g 120 -c:a aac -b:a 160k -ar 48000 -movflags +faststart "$out/manysetter.mp4"

# VP9 + Opus, two-pass constrained quality
ffmpeg -v error -y -i "$src" -c:v libvpx-vp9 -b:v 0 -crf 34 -row-mt 1 -tile-columns 2 -cpu-used 2 -g 120 \
  -pass 1 -passlogfile "$out/vp9" -an -f null /dev/null
ffmpeg -v error -y -i "$src" -c:v libvpx-vp9 -b:v 0 -crf 34 -row-mt 1 -tile-columns 2 -cpu-used 2 -g 120 \
  -pass 2 -passlogfile "$out/vp9" -c:a libopus -b:a 128k "$out/manysetter.webm"
rm -f "$out"/vp9*.log

# Posters (shown before play)
ffmpeg -v error -y -ss "$t1" -i "$src" -frames:v 1 -q:v 3 "$out/poster.jpg"
if [ -n "$t2" ]; then ffmpeg -v error -y -ss "$t2" -i "$src" -frames:v 1 -q:v 3 "$out/poster-alt.jpg"; fi
ls -la "$out"
