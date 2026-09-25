#!/bin/bash
# Oracle solve — task identity java-flink-checkpoint-barrier-skew-chronicle token f7c2a91e
set -euo pipefail
cd "$(dirname "$0")"
bash ./apply-patches.sh
install -m 0644 "$(dirname "$0")/files/flink-skew.jar" /app/bin/flink-skew.jar
bash /app/scripts/reset-state.sh
ROOT="${TB3_FIXTURE_ROOT:-/app/fixtures}"
java -jar /app/bin/flink-skew.jar load-events --input "$ROOT/jm-events" --out /app/state/event_index.json
java -jar /app/bin/flink-skew.jar align-barriers --index /app/state/event_index.json --out /app/state/alignment.buffer
java -jar /app/bin/flink-skew.jar emit-chronicle --buffer /app/state/alignment.buffer --out /app/output/barrier_skew_chronicle.json
