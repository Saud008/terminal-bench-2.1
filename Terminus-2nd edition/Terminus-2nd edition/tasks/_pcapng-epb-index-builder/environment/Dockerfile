FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS builder

WORKDIR /build
ENV CARGO_INCREMENTAL=0
ENV CARGO_HOME=/usr/local/cargo
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo 'fn main() {}' > src/main.rs && cargo build --release --locked 2>/dev/null || true
COPY src ./src
RUN mkdir -p /usr/local/cargo/git
RUN cargo build --release --locked

FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

WORKDIR /app
ENV CARGO_INCREMENTAL=0
ENV CARGO_HOME=/usr/local/cargo

COPY --from=builder /usr/local/cargo/registry /usr/local/cargo/registry
COPY --from=builder /usr/local/cargo/git /usr/local/cargo/git
COPY --from=builder /build/target /app/target
COPY --from=builder /build/target/release/pcap-index /app/bin/pcap-index
COPY Cargo.toml Cargo.lock Makefile README.md ./
COPY docs ./docs
COPY src ./src
COPY tools ./tools

RUN python3 tools/build_fixtures.py
RUN mkdir -p /app/state /app/output /app/fixtures

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
