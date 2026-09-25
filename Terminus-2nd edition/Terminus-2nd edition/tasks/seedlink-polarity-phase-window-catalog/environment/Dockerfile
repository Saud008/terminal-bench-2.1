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
COPY config/ /app/config/

RUN python3 /app/scripts/gen-fixtures.py \
    && chmod +x /app/scripts/reset-state.sh \
    && mkdir -p /app/output /app/state/phase-staging \
        /opt/verifier-fixtures/slws /opt/verifier-fixtures/leap /opt/verifier-fixtures/polarity \
        /opt/verifier-broken-slcore \
    && cp /app/tb3-bundle/tb3-leap.slws /opt/verifier-fixtures/slws/tb3-leap.slws \
    && cp /app/tb3-bundle/tb3-polarity.slws /opt/verifier-fixtures/slws/tb3-polarity.slws \
    && cp /app/tb3-bundle/tb3-shuffle.slws /opt/verifier-fixtures/slws/tb3-shuffle.slws \
    && cp /app/tb3-bundle/tb3-invariant-fail.slws /opt/verifier-fixtures/slws/tb3-invariant-fail.slws \
    && cp /app/tb3-bundle/leap-epochs.json /opt/verifier-fixtures/leap/leap-epochs.json \
    && cp /app/tb3-bundle/HV.pol /opt/verifier-fixtures/polarity/HV.pol \
    && cargo build --release -p seedcat \
    && install -m 0755 /app/target/release/seedcat /usr/local/bin/seedcat \
    && cp /app/crates/slcore/src/crc.rs /opt/verifier-broken-slcore/crc.rs \
    && cp /app/crates/slcore/src/parse.rs /opt/verifier-broken-slcore/parse.rs \
    && cp /app/crates/slcore/src/leap.rs /opt/verifier-broken-slcore/leap.rs \
    && cp /app/crates/slcore/src/polarity.rs /opt/verifier-broken-slcore/polarity.rs \
    && cp /app/crates/slcore/src/clip.rs /opt/verifier-broken-slcore/clip.rs \
    && cp /app/crates/slcore/src/picks.rs /opt/verifier-broken-slcore/picks.rs \
    && cp /app/crates/slcore/src/staging.rs /opt/verifier-broken-slcore/staging.rs \
    && cp /app/crates/slcore/src/export.rs /opt/verifier-broken-slcore/export.rs \
    && cp /app/crates/slcore/src/invariant.rs /opt/verifier-broken-slcore/invariant.rs \
    && cp /app/crates/slcore/src/digest.rs /opt/verifier-broken-slcore/digest.rs \
    && /app/scripts/reset-state.sh
