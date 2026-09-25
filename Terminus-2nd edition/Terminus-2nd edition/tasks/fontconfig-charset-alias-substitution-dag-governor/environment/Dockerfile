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

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        iniconfig==2.3.0 packaging==26.2 pluggy==1.6.0 Pygments==2.20.0 \
        pytest==9.0.3 pytest-json-ctrf==0.5.0

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY crates/fc-alias-core/Cargo.toml crates/fc-alias-core/Cargo.toml
COPY crates/fc-alias-check/Cargo.toml crates/fc-alias-check/Cargo.toml

RUN mkdir -p crates/fc-alias-core/src crates/fc-alias-check/src \
    && echo "pub fn placeholder() {}" > crates/fc-alias-core/src/lib.rs \
    && echo "fn main() {}" > crates/fc-alias-check/src/main.rs \
    && cargo fetch --locked

COPY crates/ crates/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output /app/state \
    && cargo build --locked --release -p fc-alias-check \
    && install -m 0755 target/release/fc-alias-check /usr/local/bin/fc-alias-check \
    && mkdir -p /opt/verifier-broken-fc \
    && cp /app/crates/fc-alias-core/src/parse.rs /opt/verifier-broken-fc/parse.rs \
    && cp /app/crates/fc-alias-core/src/dag.rs /opt/verifier-broken-fc/dag.rs \
    && cp /app/crates/fc-alias-core/src/resolve.rs /opt/verifier-broken-fc/resolve.rs \
    && cp /app/crates/fc-alias-core/src/staging.rs /opt/verifier-broken-fc/staging.rs \
    && bash /app/scripts/reset-state.sh
