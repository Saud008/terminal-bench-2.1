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
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app
COPY Cargo.toml Cargo.lock rust-toolchain.toml README.md /app/
COPY crates/ /app/crates/
COPY docs/ /app/docs/
COPY scripts/ /app/scripts/

RUN python3 /app/scripts/gen-fixtures.py \
    && python3 /app/scripts/gen-verifier-fixtures.py \
    && chmod +x /app/scripts/reset-state.sh \
    && mkdir -p /app/output /app/state /app/fixtures/streams \
    && cargo build --locked -p minizdecode \
    && install -m 0755 target/debug/minizdecode /usr/local/bin/minizdecode
