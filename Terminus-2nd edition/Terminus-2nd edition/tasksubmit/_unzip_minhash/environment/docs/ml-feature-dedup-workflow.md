# ML feature dedup workflow

minclus implements a three-stage machine-learning feature pipeline for near-duplicate document detection before training or inference export.

## Scan stage

minclus scan --corpus-dir <dir> --run-id <id> --profile <name>

Ingests a JSONL batch from the corpus directory, normalizes tokens, builds word-shingle feature rows, and materializes MinHash embedding signatures into /app/state/sketch-index/<run-id>.json.

## Group stage

minclus group --run-id <id> --jaccard-floor <float>

Reads the sketch index for the run id, estimates pairwise Jaccard similarity from signature rows, and links documents whose eval metric meets the floor into cluster components. Output lands in /app/work/cluster-graph/<run-id>.json.

## Attest stage

minclus attest --run-id <id> --output <path>

Reads the sketch index and cluster graph, computes singleton and cluster eval summaries, and exports a dedup provenance report JSON to the caller output path.

All stages share configuration from /app/config/minclus.json. Profile presets in /app/fixtures/run_profiles.json name default, strict, and relaxed jaccard_floor values used during batch eval.
