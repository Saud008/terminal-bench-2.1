# qasmenv workspace

Rust CLI for QASM shot-noise calibration envelope ingest, compute, and export.

Build from /app with cargo build --release --locked. Cargo.lock pins transitive crate versions for reproducible builds. The qasmenv binary installs to /app/bin/qasmenv.

Contracts live under docs/. Bundled calibration fixtures are under data/. Hidden verifier fixtures install to /opt/verifier-fixtures/qasmenv/.
