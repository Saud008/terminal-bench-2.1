FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

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
 && rm -f /tmp/requirements.lock

RUN ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
 && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
 && ln -sf /usr/local/cargo/bin/rustup /usr/local/bin/rustup

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0
ENV TB3_TYPO_DISTANCE=1

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY crates/ /app/crates/
COPY config/ /app/config/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md
COPY hidden-fixtures/ /opt/verifier-fixtures/

RUN find /app/scripts -name '*.sh' -exec sed -i 's/\r$//' {} + \
 && chmod +x /app/scripts/reset-state.sh /app/scripts/rebuild.sh \
 && cargo build --release --locked -p typesense-search-cli \
 && install -m 0755 /app/target/release/typesense-search-cli /usr/local/bin/typesense-search-cli \
 && mkdir -p /app/work /app/output /app/state \
 && bash /app/scripts/reset-state.sh
