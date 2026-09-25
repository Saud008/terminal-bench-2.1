FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv tmux asciinema \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
    && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes \
        -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

ENV PATH="/opt/verifier-venv/bin:/app/bin:/usr/local/cargo/bin:${PATH}"

COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY docs ./docs

RUN mkdir -p /opt/verifier-fixtures/witness-bundles /app/state /app/output /app/bin

RUN cargo build --release --locked --bin gen-fixtures \
    && ./target/release/gen-fixtures
