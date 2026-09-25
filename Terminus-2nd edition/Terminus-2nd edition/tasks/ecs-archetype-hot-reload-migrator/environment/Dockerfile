FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
 && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir \
    pytest==9.0.3 \
    pytest-json-ctrf==0.5.0

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

COPY Cargo.toml Cargo.lock README.md /app/
COPY crates/ecs-core/Cargo.toml crates/ecs-core/Cargo.toml
COPY crates/ecs-migrate/Cargo.toml crates/ecs-migrate/Cargo.toml

RUN mkdir -p crates/ecs-core/src crates/ecs-migrate/src \
 && echo "pub fn placeholder() {}" > crates/ecs-core/src/lib.rs \
 && echo "fn main() {}" > crates/ecs-migrate/src/main.rs \
 && cargo fetch --locked

COPY crates/ crates/
COPY docs/ docs/
COPY data/ data/
COPY fixtures/ fixtures/
COPY ingest/ ingest/
COPY decoy/ decoy/
COPY hidden-fixtures/ecs-migrate/ /opt/verifier-fixtures/ecs-migrate/
COPY scripts/ scripts/

RUN sed -i 's/\r$//' /app/scripts/*.sh \
 && chmod +x /app/scripts/*.sh \
 && python3 /app/scripts/build_templates.py \
 && python3 /app/scripts/build_tb3_fixtures.py \
 && mkdir -p /app/output \
 && cargo build --locked -p ecs-migrate \
 && install -m 0755 target/debug/ecs-migrate /usr/local/bin/ecs-migrate \
 && bash /app/scripts/reset-state.sh
