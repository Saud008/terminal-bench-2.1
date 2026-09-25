FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

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

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
 && rm -f /tmp/requirements.lock \
 && ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
 && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
 && ln -sf /usr/local/cargo/bin/rustup /usr/local/bin/rustup

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0
ENV CARGO_NET_OFFLINE=true

COPY Cargo.toml Cargo.lock ./
COPY .cargo/ .cargo/
COPY vendor.tar.gz ./
RUN tar -xzf ./vendor.tar.gz -C /app && rm ./vendor.tar.gz

COPY crates/ crates/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY hidden/ /opt/verifier-fixtures/turnctl/
COPY scripts/ scripts/
COPY README.md README.md

# Agent/verifier must rebuild turnctl after repairing combat-core sources (single-stage intentional).
RUN sed -i 's/\r$//' /app/scripts/*.sh \
 && find /app/crates /app/docs /app/fixtures /app/scripts -type f \( -name '*.rs' -o -name '*.toml' -o -name '*.md' -o -name '*.json' -o -name '*.sh' \) -exec sed -i 's/\r$//' {} + \
 && chmod +x /app/scripts/*.sh \
 && mkdir -p /app/output \
 && cargo build --offline --locked --release --bin turnctl \
 && install -m 0755 target/release/turnctl /usr/local/bin/turnctl \
 && mkdir -p /opt/verifier-broken-combat \
 && cp /app/crates/combat-core/src/ingest.rs /opt/verifier-broken-combat/ingest.rs \
 && cp /app/crates/combat-core/src/scheduler.rs /opt/verifier-broken-combat/scheduler.rs \
 && cp /app/crates/combat-core/src/bleed.rs /opt/verifier-broken-combat/bleed.rs \
 && cp /app/crates/combat-core/src/export.rs /opt/verifier-broken-combat/export.rs \
 && cp /app/crates/combat-core/src/simulate.rs /opt/verifier-broken-combat/simulate.rs \
 && bash /app/scripts/reset-state.sh
