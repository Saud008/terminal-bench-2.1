FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app
COPY Cargo.toml /app/Cargo.toml
COPY crates/ /app/crates/
COPY docs/ /app/docs/
COPY scripts/ /app/scripts/

RUN python3 /app/scripts/gen-fixtures.py \
    && chmod +x /app/scripts/reset-state.sh \
    && mkdir -p /app/output /app/state/lap-staging /opt/verifier-fixtures/fit /opt/verifier-broken-fit \
    && cp /app/fixtures/fit/shuffle-start-time.fit /opt/verifier-fixtures/fit/tb3-shuffle.fit \
    && cp /app/fixtures/fit/decode-align-fail.fit /opt/verifier-fixtures/fit/tb3-align.fit \
    && cp /app/fixtures/fit/tempo.fit /opt/verifier-fixtures/fit/tb3-tempo.fit \
    && cargo build --release -p fitlap \
    && install -m 0755 /app/target/release/fitlap /usr/local/bin/fitlap \
    && cp /app/crates/fitcore/src/crc.rs /opt/verifier-broken-fit/crc.rs \
    && cp /app/crates/fitcore/src/staging.rs /opt/verifier-broken-fit/staging.rs \
    && cp /app/crates/fitcore/src/boundary.rs /opt/verifier-broken-fit/boundary.rs \
    && cp /app/crates/fitcore/src/export.rs /opt/verifier-broken-fit/export.rs \
    && cp /app/crates/fitcore/src/trigger.rs /opt/verifier-broken-fit/trigger.rs \
    && /app/scripts/reset-state.sh
