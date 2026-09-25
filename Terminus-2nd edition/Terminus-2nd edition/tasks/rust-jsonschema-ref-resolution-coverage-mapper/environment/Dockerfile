# syntax=docker/dockerfile:1
FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        tmux \
        asciinema \
        python3 \
        python3-venv \
        python3-pip \
        patch \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier \
    && /opt/verifier/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

ENV PATH=/opt/verifier/bin:/usr/local/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV CARGO_TARGET_DIR=/app/environment/target

WORKDIR /app/environment
COPY Cargo.toml ./
COPY crates ./crates
COPY tools ./tools
COPY fixtures ./fixtures
COPY docs ./docs
COPY scripts ./scripts
COPY .dockerignore ./

RUN cargo build --release -p jscovmap \
    && mkdir -p tools/jscovmap \
    && install -m 0755 target/release/jscovmap tools/jscovmap/jscovmap \
    && chmod +x scripts/*.sh \
    && ln -sf docs /app/docs \
    && mkdir -p /app/state /app/output /opt/verifier-fixtures/jscov_hidden/schemas \
    && cp fixtures/hidden_schemas/ledger.json /opt/verifier-fixtures/jscov_hidden/schemas/ledger.json \
    && cp fixtures/hidden_examples.jsonl /opt/verifier-fixtures/jscov_hidden/examples.jsonl

WORKDIR /app
