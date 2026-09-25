# Submission explanations — bash-steamcmd-workshop-mount-plan-pipeline

**Task folder:** tasks/bash-steamcmd-workshop-mount-plan-pipeline/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must implement a four-stage workshop-plan pipeline where ingest writes a digest-bound staging snapshot, dependency resolution applies numeric semver and required-edge rules, topological sort emits contract cycle paths, and export validates staging before publishing JSON. The prior spec contradiction on cycle traversal fooled careful readers who followed the embedded example instead of the dependency-first adjacency rule. Partial fixes pass bundled fixtures but fail hidden semver traps, four-mod cycle walks, staging digest consistency across epochs, Kahn batch ASCII ordering, and cross-run run_seq persistence including failed-run footer seals. Behavioral tests drive workshop-plan end-to-end on varied synthetic manifests and independent reference recomputation; they do not require a particular lib/*.sh source wiring.

## Solution Explanation

The oracle runs make install to place corrected ingest, staging, deps, topo, and export modules, rebuilds scripts, then drives workshop-plan on a catalog fixture. Ingest commits parsed-manifest.tsv and staging-meta.json. Deps builds the required-edge graph with numeric semver. Topo runs layer-by-layer Kahn sort and walks cycles along first outgoing dependency-to-dependent edges. Export verifies the staging SHA-256, updates run-seq.json from the manifest and config fingerprint only on exit 0, and writes the plan footer. Failed runs seal footer.run_seq as 1 with no prior state (or retain the prior seq) without persisting. A second identical successful run keeps run_seq stable.

## Verification Explanation

test.sh resets state, runs rebuild-workshop.sh, and pytest calls workshop-plan via subprocess on every test. reference_plan.py recomputes expected JSON independently. Stage behaviors are exercised through varied end-to-end inputs (Kahn ASCII batches, diamond graphs, numeric vs rejecting semver pairs, alternate cycle paths, staging snapshot replacement, and failed-run sequence seals) rather than swapping golden/broken lib layers. Hidden fixtures under /opt/verifier-fixtures/workshop cover numeric semver 1.10.0 versus >=1.2.0 and a four-mod cycle path. Oracle scores 1.0 and NOP 0.0 on the broken baseline image.

## Category note

Zip metadata uses `system-administration` (host-local workshop-plan mount-plan ops control plane: admit VDF → staging digest / semver gates → sealed plan export). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior upload failed Harbor `[category_classifier]` as blocked `software-engineering` under weaker control-path framing; keep the ops control-plane language and the explicit “not a SteamCMD CLI rebuild / bash pipeline engineering / pytest harness” negation.
