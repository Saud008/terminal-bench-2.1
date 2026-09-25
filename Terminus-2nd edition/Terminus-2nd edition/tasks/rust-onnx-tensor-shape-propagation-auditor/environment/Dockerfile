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
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier \
    && /opt/verifier/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

ENV PATH=/opt/verifier/bin:/usr/local/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV CARGO_TARGET_DIR=/app/environment/target
ENV PYTHONPATH=/app/environment/support

WORKDIR /app
COPY Cargo.toml /app/environment/Cargo.toml
COPY vlx_core /app/environment/vlx_core
COPY docs /app/environment/docs
COPY fixtures/graphs /app/environment/fixtures/graphs
COPY scripts /app/environment/scripts
COPY tools /app/environment/tools
COPY support /app/environment/support

RUN cd /app/environment \
    && cargo build --release -p shapeprop \
    && install -m 0755 target/release/shapeprop /app/environment/tools/shapeprop/shapeprop \
    && chmod +x /app/environment/scripts/*.sh \
    && ln -sf /app/environment/docs /app/docs \
    && mkdir -p /app/state /app/output
