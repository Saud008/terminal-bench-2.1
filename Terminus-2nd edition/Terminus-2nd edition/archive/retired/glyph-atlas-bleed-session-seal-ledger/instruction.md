Glyph atlas session administrators run the host-local atlasd glyph-sheet bleed session control plane at /usr/local/bin/atlaspack. Each offline ops pass admits catalog JSON and sprite sheets from /app/fixtures/, enforces padding, UV-bleed, rotation, seed-scale, and oversized admission gates, stages atlas packing state, then publishes sealed PNG atlas and checksum manifest exports only after those gates pass. There is no remote asset CDN. This is a system-administration host-local glyph atlas bleed session ops control plane; keep catalog admission, pad-bleed gates, UV sample audits, and sealed export aligned. It is not a generic service repair exercise.

Read the ops contracts under /app/docs/ before changing behavior: /app/docs/atlas-ops-workflow.md for the control-plane overview, /app/docs/atlas-contract.md for padding bleed UV rotation and size gates, /app/docs/manifest-schema.md for sealed manifest fields and checksum policy, /app/docs/exit-codes.md for pack and probe exit obligations, and /app/docs/atlas-runtime-paths.md for fixture and output paths.

atlaspack pack --catalog PATH --sprites PATH --set NAME --seed N --atlas-out PATH --manifest-out PATH must admit one catalog set, apply pad-bleed rotation and scale gates, and publish sealed atlas PNG plus manifest JSON at the caller-provided output paths only when admission succeeds.

atlaspack probe --atlas PATH --manifest PATH --glyph ID --frame N --u U --v V must audit a sealed atlas sample at normalized UV coordinates for one glyph frame and exit per /app/docs/exit-codes.md.

Example ops passes:

atlaspack pack --catalog /app/fixtures/catalog.json --sprites /app/fixtures/sprites --set core-glyphs --seed 7 --atlas-out /app/output/atlas.png --manifest-out /app/output/manifest.json

atlaspack probe --atlas /app/output/atlas.png --manifest /app/output/manifest.json --glyph arrow --frame 0 --u 0.0 --v 0.0

Optional environment overlays for verifier fixtures may set TB3_VERIFIER_FIXTURES when tests document it. The control plane is rebuilt from /app sources before checks. Do not edit /app/docs/, files under /app/fixtures/, or files under /tests/.
