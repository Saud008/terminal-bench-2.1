# Conform workflow

## Editorial context

An edit decision list names record-in/record-out positions on a master timeline plus source-in/source-out handles on camera reels. Conform auditors compare those spans against fps and drop-frame flags in the bundle timecode map, resolve reel aliases used on the floor versus vault naming, and flag offline media before declaring orphan reels.

## Stage responsibilities

Stage reads bundle.json, validates FCM against the map, parses CMX events, converts timecodes, resolves aliases, evaluates handle budgets, and applies offline media suppression for missing inventory.

Output is a single sealed JSON file at /app/state/edl-conform-sealed.json containing edits, diagnostics, seal_digest, bundle fingerprint, and run_seq.

## Publish responsibilities

Publish loads only edl-conform-sealed.json and writes /app/output/conform-atlas.json. It must not re-read bundle EDL paths, source reel tables, alias files, or missing lists. Diagnostics copy forward with severity weights from /app/config/severity-weights.json.

## Timecode map coupling

When drop_frame is true in the map, minute-boundary corrections apply separately to record and source spans. Non-drop maps use linear frame arithmetic at the map fps.

## Cross-run fingerprinting

run_seq in /app/state/run-seq.json increments only when bundle fingerprint changes. Re-sealing an identical bundle reproduces seal_digest and run_seq.
