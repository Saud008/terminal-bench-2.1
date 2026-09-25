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

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

RUN ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
    && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
    && ln -sf /usr/local/cargo/bin/rustup /usr/local/bin/rustup

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0
ENV CARGO_BUILD_JOBS=2
ENV RUSTFLAGS="-C debuginfo=0"

WORKDIR /app

COPY Cargo.toml Cargo.lock rust-toolchain.toml README.md /app/
COPY crates/docmodel/Cargo.toml crates/docmodel/Cargo.toml
COPY crates/docsync/Cargo.toml crates/docsync/Cargo.toml
COPY crates/docdiag/Cargo.toml crates/docdiag/Cargo.toml
COPY crates/docexport/Cargo.toml crates/docexport/Cargo.toml
COPY crates/term-lsp/Cargo.toml crates/term-lsp/Cargo.toml

RUN mkdir -p crates/docmodel/src crates/docsync/src crates/docdiag/src crates/docexport/src crates/term-lsp/src \
    && echo "pub fn placeholder() {}" > crates/docmodel/src/lib.rs \
    && echo "pub fn placeholder() {}" > crates/docsync/src/lib.rs \
    && echo "pub fn placeholder() {}" > crates/docdiag/src/lib.rs \
    && echo "pub fn placeholder() {}" > crates/docexport/src/lib.rs \
    && echo "fn main() {}" > crates/term-lsp/src/main.rs \
    && cargo fetch --locked

COPY crates/ crates/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY hidden-fixtures/ /opt/verifier-fixtures/lsp-doclint/
COPY scripts/ scripts/

RUN find /app/scripts -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output /app/state \
    && cargo build --locked --release -p term-lsp \
    && install -m 0755 target/release/term-lsp /usr/local/bin/term-lsp \
    && find /app/fixtures -type f -exec chmod a-w {} + \
    && bash /app/scripts/reset-state.sh
