FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update && apt-get install -y --no-install-recommends \
    asciinema \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

ENV CARGO_INCREMENTAL=0

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release --locked

RUN mkdir -p /opt/verifier-scripts \
    && printf '%s\n' \
    '#!/bin/bash' \
    'set -euo pipefail' \
    'cd /app' \
    '/usr/local/cargo/bin/cargo build --release --locked' \
    > /opt/verifier-scripts/rebuild-s5lineage \
    && chmod +x /opt/verifier-scripts/rebuild-s5lineage

ENV PATH="/usr/local/cargo/bin:/app/target/release:/opt/verifier-scripts:/opt/verifier-venv/bin:${PATH}"

COPY docs ./docs
COPY fixtures ./fixtures
COPY verifier-fixtures /opt/verifier-fixtures

RUN mkdir -p /app/state /app/output
