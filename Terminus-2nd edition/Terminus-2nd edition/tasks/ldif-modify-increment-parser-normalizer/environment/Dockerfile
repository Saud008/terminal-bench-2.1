FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/verifier-venv

COPY requirements.txt /tmp/requirements.txt
RUN /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt \
    && ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
    && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
    && ln -sf /usr/local/cargo/bin/rustup /usr/local/bin/rustup

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY crates/ldif-core/Cargo.toml crates/ldif-core/Cargo.toml
COPY crates/ldif-apply/Cargo.toml crates/ldif-apply/Cargo.toml

RUN mkdir -p crates/ldif-core/src crates/ldif-apply/src \
    && echo "pub fn placeholder() {}" > crates/ldif-core/src/lib.rs \
    && echo "fn main() {}" > crates/ldif-apply/src/main.rs \
    && cargo fetch --locked

COPY crates/ crates/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output \
    && cargo build --locked --release --bin ldif-apply \
    && install -m 0755 target/release/ldif-apply /usr/local/bin/ldif-apply \
    && mkdir -p /opt/verifier-broken-ldif \
    && cp /app/crates/ldif-core/src/parser.rs /opt/verifier-broken-ldif/parser.rs \
    && cp /app/crates/ldif-core/src/apply.rs /opt/verifier-broken-ldif/apply.rs \
    && cp /app/crates/ldif-core/src/audit.rs /opt/verifier-broken-ldif/audit.rs \
    && bash /app/scripts/reset-state.sh
