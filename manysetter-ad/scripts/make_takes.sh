#!/usr/bin/env bash
# Generate N verified takes of a script with one voice. Usage: make_takes.sh <voice> <script.txt> <name> <n>
set -u
voice=$1; script=$2; name=$3; n=$4
style="$(cat vo/style_$(echo "$voice" | tr 'A-Z' 'a-z').txt 2>/dev/null)"
ok=0; attempt=0
while [ $ok -lt "$n" ] && [ $attempt -lt $((n * 3)) ]; do
  attempt=$((attempt + 1))
  out="vo/takes/${name}_${voice}_t${attempt}.wav"
  python3 scripts/tts_gemini.py --voice "$voice" --text-file "$script" --style "$style" --no-fallback --out "$out" || { sleep 21; continue; }
  if python3 scripts/check_vo.py "$out" "$script"; then ok=$((ok + 1)); echo "PASS $out"; else echo "FAIL $out"; mv "$out" "${out%.wav}.rejected.wav"; fi
  sleep 21
done
echo "done: $ok verified takes for $name"
