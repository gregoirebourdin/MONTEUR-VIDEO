#!/usr/bin/env bash
# Full script v3 takes for several voices, strict word-by-word QA, up to 3 tries per voice.
cd "$(dirname "$0")/.."
for v in "$@"; do
  for try in 1 2 3; do
    out="vo/takes_v3/${v}.wav"
    python3 scripts/tts_gemini.py --voice "$v" --segments vo/script_v3_segments.json --no-fallback --out "$out" 2>&1 | tail -c 150
    python3 scripts/check_vo.py "$out" vo/script_v3_segments.json > "vo/takes_v3/${v}.qa.txt"; rc=$?
    tail -3 "vo/takes_v3/${v}.qa.txt"
    if [ $rc -eq 0 ]; then echo "PASS $v (try $try)"; break; fi
    cp "$out" "vo/takes_v3/${v}.try${try}.rejected.wav"; echo "FAIL $v (try $try)"
  done
done
