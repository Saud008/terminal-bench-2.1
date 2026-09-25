# Platform rubric — brat-span-relation-consensus-exporter

**Task folder:** tasks/brat-span-relation-consensus-exporter/
**Written:** 2026-07-28T18:45:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent normalizes span offsets using revision_map shifts into staging rows before overlap resolution, +3
Agent resolves overlapping spans by highest annotator weight not shortest length, +3
Agent sums annotator weights into consensus span and relation scores, +3
Agent preserves adjudication-locked spans and drops overlapping unlocked competitors, +3
Agent exports relations with arg1_span and arg2_span without swapping endpoints, +3
Agent maps annotator-local span ids through annotator-namespaced keys before relation export, +2
Agent writes consensus_digest as sha256 over canonical sorted span and relation keys, +3
Agent rejects export when consensus staging_generation or project_digest drifts from staging, +2
Agent reads consensus-generation.json during export without re-ingesting project files, +2
Agent materializes annotation-stage.json before consensus and export stages, +1
Agent picks shortest overlapping span regardless of annotator weight, -3
Agent ignores revision_map offset shifts leaving superseded revision coordinates, -3
Agent counts one vote per annotator ignoring configured weight values, -3
Agent drops adjudication-locked spans during overlap resolution, -3
Agent swaps relation arg1_span and arg2_span during direction normalization, -3
Agent resolves bare colliding local span ids across annotators, -2
Agent emits md5 consensus_digest or re-reads live annotation projects at export, -2
