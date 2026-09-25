FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    build-essential \
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

RUN ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
 && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
 && ln -sf /usr/local/cargo/bin/rustup /usr/local/bin/rustup

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

COPY Cargo.toml Cargo.lock ./
COPY crates/lootsettle-core/Cargo.toml crates/lootsettle-core/Cargo.toml
COPY crates/lootsettle-cli/Cargo.toml crates/lootsettle-cli/Cargo.toml

RUN mkdir -p crates/lootsettle-core/src crates/lootsettle-cli/src \
 && echo "pub fn placeholder() {}" > crates/lootsettle-core/src/lib.rs \
 && echo "fn main() {}" > crates/lootsettle-cli/src/main.rs \
 && cargo fetch --locked

COPY crates/ crates/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY fixtures-tb3/ /opt/verifier-fixtures/
COPY scripts/ scripts/

RUN sed -i 's/\r$//' /app/scripts/*.sh \
 && chmod +x /app/scripts/*.sh \
 && mkdir -p /app/output /app/state \
 && cargo build --locked --release -p lootsettle-cli \
 && install -m 0755 target/release/lootsettle /usr/local/bin/lootsettle \
 && bash /app/scripts/reset-state.sh
