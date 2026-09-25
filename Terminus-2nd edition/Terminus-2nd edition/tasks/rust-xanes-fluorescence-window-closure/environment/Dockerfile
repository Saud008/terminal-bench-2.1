FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

RUN ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
    && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
    && ln -sf /usr/local/cargo/bin/rustup /usr/local/bin/rustup

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY crates/xanes-core/Cargo.toml crates/xanes-core/Cargo.toml
COPY crates/xanes-cli/Cargo.toml crates/xanes-cli/Cargo.toml

RUN mkdir -p crates/xanes-core/src crates/xanes-cli/src \
    && echo "pub fn placeholder() {}" > crates/xanes-core/src/lib.rs \
    && echo "fn main() {}" > crates/xanes-cli/src/main.rs \
    && cargo fetch --locked

COPY crates/ crates/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output \
    && cargo build --locked --release --bin xanesctl \
    && install -m 0755 target/release/xanesctl /usr/local/bin/xanesctl \
    && mkdir -p /opt/verifier-broken-xanes \
    && cp /app/crates/xanes-core/src/victoreen_fit.rs /opt/verifier-broken-xanes/victoreen_fit.rs \
    && cp /app/crates/xanes-core/src/edge_ordinal.rs /opt/verifier-broken-xanes/edge_ordinal.rs \
    && cp /app/crates/xanes-core/src/mu_window_seal.rs /opt/verifier-broken-xanes/mu_window_seal.rs \
    && mkdir -p /opt/verifier-fixtures/xanes-delta/traces /opt/verifier-fixtures/xanes-delta/windows \
    && cp -r /app/fixtures/hidden/traces/. /opt/verifier-fixtures/xanes-delta/traces/ \
    && cp -r /app/fixtures/hidden/windows/. /opt/verifier-fixtures/xanes-delta/windows/ \
    && bash /app/scripts/reset-state.sh
