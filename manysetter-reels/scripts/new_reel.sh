#!/usr/bin/env bash
# Start a new reel from reel1 (the reference): same engine, Setty, captions, props and sound kit.
# Usage: scripts/new_reel.sh reel2
set -euo pipefail
cd "$(dirname "$0")/.."
id="${1:?usage: scripts/new_reel.sh reelN}"
[ -e "$id" ] && { echo "$id already exists"; exit 1; }
mkdir -p "$id/src" "$id/audio" "vo/$id" vo/takes
cp reel1/build.py reel1/audio.py reel1/hyperframes.json "$id/"
cp reel1/src/template.html "$id/src/template.html"
ln -s ../assets "$id/assets"
cat > "vo/${id}_segments.json" <<'JSON'
[
 {"text": "Hey, bitch.", "style": "Smug, slow, sassy greeting, like a best friend about to roast you. A little drawn out."},
 {"text": "You did your fucking webinar, right?", "style": "Cheeky and mocking, quick."}
]
JSON
echo "created $id/ and vo/${id}_segments.json"
echo "next: write the script in vo/${id}_segments.json, then follow CLAUDE.md § Pipeline"
