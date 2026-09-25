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

WORKDIR /app
COPY Cargo.toml /app/environment/Cargo.toml
COPY src /app/environment/src
COPY docs /app/environment/docs
COPY registry /app/environment/registry
COPY scripts /app/environment/scripts
COPY hidden /app/environment/hidden
COPY verifier_contracts /app/environment/verifier_contracts

RUN mkdir -p /app/var /app/lineage /app/bin /opt/verifier-fixtures/xr7_probe/catalogs /opt/verifier-fixtures/xr7_probe/weights \
    && cd /app/environment \
    && cargo build --release \
    && install -m 0755 target/release/xr7 /app/bin/xr7 \
    && chmod +x /app/environment/scripts/*.sh \
    && ln -sf /app/environment/docs /app/docs \
    && cp -r /app/environment/hidden/catalogs/. /opt/verifier-fixtures/xr7_probe/catalogs/ \
    && cp -r /app/environment/hidden/weights/. /opt/verifier-fixtures/xr7_probe/weights/
