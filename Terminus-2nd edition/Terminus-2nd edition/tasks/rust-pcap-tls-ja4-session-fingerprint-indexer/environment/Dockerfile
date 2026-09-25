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

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier \
    && /opt/verifier/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

ENV PATH=/opt/verifier/bin:/usr/local/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV CARGO_TARGET_DIR=/app/environment/target

WORKDIR /app
COPY Cargo.toml Cargo.lock /app/environment/
COPY tls_lab /app/environment/tls_lab
COPY docs /app/environment/docs
COPY fixtures /app/environment/fixtures
COPY scripts /app/environment/scripts
COPY tools /app/environment/tools

RUN cd /app/environment \
    && cargo build --release --locked -p ja4idx \
    && install -m 0755 target/release/ja4idx /app/environment/tools/ja4idx/ja4idx \
    && chmod +x /app/environment/scripts/*.sh \
    && ln -sf /app/environment/docs /app/docs \
    && mkdir -p /app/state /app/output
