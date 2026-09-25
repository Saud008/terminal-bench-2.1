FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV CARGO_INCREMENTAL=0

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY crates/qwindex-core/Cargo.toml crates/qwindex-core/Cargo.toml
COPY crates/qwindex-cli/Cargo.toml crates/qwindex-cli/Cargo.toml

RUN mkdir -p crates/qwindex-core/src crates/qwindex-cli/src \
    && echo "pub fn placeholder() {}" > crates/qwindex-core/src/lib.rs \
    && echo "fn main() {}" > crates/qwindex-cli/src/main.rs \
    && cargo fetch --locked

COPY crates/ crates/

RUN cargo build --locked --release --bin qwindex

FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

# Agents and the verifier recompile qwindex (rusqlite bundled) after source edits.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app

COPY --from=builder /usr/local/cargo /usr/local/cargo
COPY --from=builder /app/Cargo.toml /app/Cargo.lock ./
COPY --from=builder /app/crates /app/crates
COPY --from=builder /app/target /app/target

COPY docs/ docs/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md README.md

RUN mkdir -p /opt/verifier-fixtures/qwindex/hidden \
    && cp fixtures/hidden/batch_delete.jsonl /opt/verifier-fixtures/qwindex/hidden/batch_delete.jsonl \
    && rm -rf /app/fixtures/hidden

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/data /app/state /app/output \
    && install -m 0755 target/release/qwindex /usr/local/bin/qwindex \
    && bash /app/scripts/reset-state.sh
