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

WORKDIR /app/environment
COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts

RUN cargo build --release --locked -p agerecv \
    && install -D -m 0755 target/release/agerecv /app/environment/bin/agerecv \
    && chmod +x /app/environment/scripts/*.sh \
    && ln -sf /app/environment/docs /app/docs \
    && mkdir -p /app/state /app/output /opt/verifier-fixtures/age_hidden \
    && cp -r /app/environment/fixtures/hidden_corpus/. /opt/verifier-fixtures/age_hidden/
