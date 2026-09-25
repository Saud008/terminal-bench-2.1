The grid navmesh toolchain at `/usr/local/bin/navmeshctl` validates JSON cell bundles and runs Q16.16 fixed-point path queries in one shot. It is not the tiled `navctl` build-graph / publish pipeline. Client-visible `validate` and `path` exports disagree with `/app/docs/spec.md`, `/app/docs/mesh-format.md`, and `/app/docs/validate-contract.md`.

Repair the Rust modules under `/app/crates/navmesh-core/src/` so validate and path outputs match the contract for bundled meshes and seed-derived link perturbations.

The environment has no outbound network access. Do not edit `/app/docs/`, `/app/fixtures/`, or `/tests/`.
