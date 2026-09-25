FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="rust-geoip-prefix-overlap-routing-curator" \
      org.opencontainers.image.description="Host-local geocur prefix admission and overlap atlas ops" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip tmux asciinema \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY netpfx ./netpfx
COPY rank_sel ./rank_sel
COPY scope_fit ./scope_fit
COPY prov_chart ./prov_chart
COPY stg_wal ./stg_wal
COPY reconcile ./reconcile
COPY atlas_out ./atlas_out
COPY ingest ./ingest
COPY model ./model
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts

RUN mkdir -p /app/state /app/work /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-state.sh \
    && cargo build --release --locked \
    && cp /app/target/release/geocur /app/bin/geocur

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
