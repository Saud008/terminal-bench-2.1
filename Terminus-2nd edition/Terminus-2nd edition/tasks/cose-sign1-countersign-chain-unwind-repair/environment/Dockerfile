FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
        libsqlite3-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app
COPY Cargo.toml Cargo.lock rust-toolchain.toml README.md /app/
COPY crates/ /app/crates/
COPY docs/ /app/docs/
COPY scripts/ /app/scripts/

RUN /opt/verifier-venv/bin/python3 /app/scripts/gen-fixtures.py \
    && chmod +x /app/scripts/reset-state.sh \
    && mkdir -p /app/output /app/state \
    && cargo build --locked -p cose-audit \
    && install -m 0755 target/debug/cose-audit /usr/local/bin/cose-audit \
    && mkdir -p /opt/verifier-fixtures \
    && cp -a /app/opt/verifier-fixtures/. /opt/verifier-fixtures/ \
    && rm -rf /app/opt
