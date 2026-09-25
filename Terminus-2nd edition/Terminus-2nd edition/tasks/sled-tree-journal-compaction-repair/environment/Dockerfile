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

RUN python3 -m venv /opt/verifier-venv
COPY requirements.lock /tmp/requirements.lock
RUN /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

RUN ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
    && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
    && ln -sf /usr/local/cargo/bin/rustup /usr/local/bin/rustup

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY crates/sled_engine/Cargo.toml crates/sled_engine/Cargo.toml
COPY crates/sledtool/Cargo.toml crates/sledtool/Cargo.toml
COPY crates/sled_engine/src/lib.rs crates/sled_engine/src/lib.rs

RUN mkdir -p crates/sled_engine/src/btree crates/sled_engine/src/commit \
    crates/sled_engine/src/compaction crates/sled_engine/src/decoy \
    crates/sled_engine/src/export crates/sled_engine/src/ingest \
    crates/sled_engine/src/journal crates/sled_engine/src/page \
    crates/sled_engine/src/snapshot crates/sled_engine/src/staging \
    crates/sled_engine/src/storage crates/sledtool/src \
    && printf 'pub fn placeholder() {}\n' > crates/sled_engine/src/btree/mod.rs \
    && echo 'fn main() {}' > crates/sledtool/src/main.rs \
    && cargo fetch --locked

COPY crates/ crates/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY config/ config/
COPY scripts/ scripts/
COPY opt-verifier-fixtures/ /opt/verifier-fixtures/
COPY README.md README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output /app/state /app/state/pins \
    && cargo build --locked --release --bin sledtool \
    && install -m 0755 target/release/sledtool /usr/local/bin/sledtool \
    && bash /app/scripts/reset-state.sh
