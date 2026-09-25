FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates tmux asciinema python3 python3-venv python3-pip patch \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
       pytest==9.0.3 pytest-json-ctrf==0.5.0

ENV PATH="/opt/verifier-venv/bin:/usr/local/cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ENV CARGO_TARGET_DIR=/app/environment/target
ENV PYTHONPATH="/app/support"

WORKDIR /app
COPY Cargo.toml Cargo.lock /app/environment/
COPY src /app/environment/src
COPY docs /app/docs
COPY fixtures /app/fixtures
COPY support /app/support
COPY scripts /app/scripts
COPY hidden /opt/verifier-fixtures/whres

RUN mkdir -p /app/state /app/work /app/output /app/bin \
    && cd /app/environment \
    && cargo build --release --locked \
    && install -m 0755 target/release/whres /app/bin/whres \
    && chmod +x /app/scripts/*.sh
