FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
 && rm -rf /var/lib/apt/lists/* \
 && command -v tmux >/dev/null \
 && command -v asciinema >/dev/null

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
 && rm -f /tmp/requirements.lock

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0
ENV RUSTFLAGS="-C debuginfo=0"

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY crates/ /app/crates/
COPY fixtures/ /app/fixtures/
COPY docs/ /app/docs/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md

RUN find /app/fixtures /app/scripts -type f \( -name '*.json' -o -name '*.sh' \) -exec sed -i 's/\x0d$//' {} + \
 && chmod +x /app/scripts/reset-state.sh /app/scripts/verifier-rebuild.sh \
 && mkdir -p /app/output /app/state /opt/verifier-broken-archecore \
 && cp /app/crates/archecore/src/migrate/journal.rs /opt/verifier-broken-archecore/journal.rs \
 && cp /app/crates/archecore/src/migrate/runner/mod.rs /opt/verifier-broken-archecore/runner.rs \
 && cp /app/crates/archecore/src/migrate/ledger/mod.rs /opt/verifier-broken-archecore/ledger.rs \
 && cp /app/crates/archecore/src/storage/world.rs /opt/verifier-broken-archecore/world.rs \
 && cp /app/crates/archecore/src/storage/component.rs /opt/verifier-broken-archecore/component.rs \
 && cp /app/crates/archecore/src/storage/sparse.rs /opt/verifier-broken-archecore/sparse.rs \
 && cp /app/crates/archecore/src/storage/archetype.rs /opt/verifier-broken-archecore/archetype.rs \
 && cp /app/crates/archecore/src/query/cache.rs /opt/verifier-broken-archecore/cache.rs \
 && cp /app/crates/archecore/src/query/planner.rs /opt/verifier-broken-archecore/planner.rs \
 && cp /app/crates/archecore/src/staging/snapshot.rs /opt/verifier-broken-archecore/snapshot.rs \
 && cp /app/crates/archecore/src/export/publish.rs /opt/verifier-broken-archecore/publish.rs \
 && cp /app/crates/archecore/src/export/wrap.rs /opt/verifier-broken-archecore/wrap.rs \
 && cargo build --locked --release -p archectl \
 && install -m 0755 /app/target/release/archectl /usr/local/bin/archectl \
 && /app/scripts/reset-state.sh
