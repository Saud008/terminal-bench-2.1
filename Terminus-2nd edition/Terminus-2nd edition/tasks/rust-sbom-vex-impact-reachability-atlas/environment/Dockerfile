FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip tmux asciinema patch \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY docs ./docs
COPY data ./data
COPY config ./config
COPY scripts ./scripts
COPY verifier-fixtures/vex-bundles /opt/verifier-fixtures/vex-bundles

RUN mkdir -p /app/state /app/output /app/bin \
    && cargo build --release --locked \
    && cp /app/target/release/vexatlas /app/bin/vexatlas

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
