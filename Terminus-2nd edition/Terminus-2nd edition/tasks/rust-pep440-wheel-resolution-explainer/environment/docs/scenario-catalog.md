# Scenario catalog

Bundled scenarios live under /app/fixtures/scenarios/. Each directory contains scenario.json plus indices/*.json wheel rows. When WHRES_SCENARIO_ROOT is set, load reads scenario directories from that root instead.

## httpx-pin-requests

Baseline integration scenario at /app/fixtures/scenarios/httpx-pin-requests/. Verifier run ids include run-alpha, run-bravo, and run-chain.

## Packages exercised by bundled scenarios

| Package | Scenario | Focus |
|---------|----------|-------|
| orbit-sdk | tilde-order | PEP 440 tilde / pre-release versus final release ordering |
| numpy-lite | marker-py310 | requires_python / python_version marker evaluation |
| crypt-bind | wheel-abi3 | abi3 wheel tag compatibility on newer CPython |
| legacy-io | yanked-drop | Yanked release exclusion from the candidate pool |
| schema-kit | constraint-range | Inclusive upper-bound specifier matching |
| redis-cache | dual-index | Multi-index union and source selection |

## Reason codes

wheel_match means a compatible non-yanked wheel was selected. no_candidate means no row satisfied markers, specifiers, and tags.
