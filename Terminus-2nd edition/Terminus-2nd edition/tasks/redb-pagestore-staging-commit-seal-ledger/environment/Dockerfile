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
COPY src/lib.rs src/lib.rs
COPY src/main.rs src/main.rs
COPY src/walk.rs src/walk.rs

RUN mkdir -p src/btree src/commit src/decoy src/export src/ingest src/staging src/storage \
    && printf 'pub mod btree;\npub mod commit;\npub mod decoy;\npub mod export;\npub mod ingest;\npub mod staging;\npub mod storage;\npub mod walk;\npub const ORDER: usize = 4;\n' > src/lib.rs \
    && echo 'pub fn placeholder() {}' > src/btree/mod.rs \
    && echo 'pub fn placeholder() {}' > src/commit/mod.rs \
    && echo 'pub fn placeholder() {}' > src/decoy/mod.rs \
    && echo 'pub fn placeholder() {}' > src/export/mod.rs \
    && echo 'pub fn placeholder() {}' > src/ingest/mod.rs \
    && echo 'pub fn placeholder() {}' > src/staging/mod.rs \
    && echo 'pub fn placeholder() {}' > src/storage/mod.rs \
    && cargo fetch --locked

COPY src/ src/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY config/ config/
COPY scripts/ scripts/
COPY opt-verifier-fixtures/ /opt/verifier-fixtures/
COPY README.md README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output /app/state \
    && cargo build --locked --release --bin redbtool \
    && install -m 0755 target/release/redbtool /usr/local/bin/redbtool \
    && bash /app/scripts/reset-state.sh
