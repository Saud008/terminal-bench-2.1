FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY crates/replic-lag-core/Cargo.toml crates/replic-lag-core/Cargo.toml
COPY crates/replic-lag-cli/Cargo.toml crates/replic-lag-cli/Cargo.toml

RUN mkdir -p crates/replic-lag-core/src crates/replic-lag-cli/src \
    && echo "pub fn placeholder() {}" > crates/replic-lag-core/src/lib.rs \
    && echo "fn main() {}" > crates/replic-lag-cli/src/main.rs \
    && cargo fetch --locked

COPY crates/ crates/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md README.md

RUN mkdir -p /opt/verifier-fixtures/replic-lag/packet_loss \
    && cp fixtures/hidden/packet_loss/ingest.jsonl /opt/verifier-fixtures/replic-lag/packet_loss/ingest.jsonl \
    && rm -rf /app/fixtures/hidden

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/data /app/state /app/output \
    && cargo build --locked --release --bin replag-sim \
    && install -m 0755 target/release/replag-sim /usr/local/bin/replag-sim \
    && bash /app/scripts/reset-state.sh
