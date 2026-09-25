FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="rust-hexmap-fog-visibility-turn-planner" \
      org.opencontainers.image.description="Hex fog-of-war tactics playtest planner verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip tmux asciinema \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==9.0.3 \
    pytest-json-ctrf==0.5.0

COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY tb3_mdist ./tb3_mdist
COPY hx_place ./hx_place
COPY tb3_sray ./tb3_sray
COPY tb3_vlay ./tb3_vlay
COPY tb3_scope ./tb3_scope
COPY tb3_rout ./tb3_rout
COPY tb3_pclk ./tb3_pclk
COPY scout_decoy ./scout_decoy
COPY model ./model
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/fogpf

RUN mkdir -p /app/state/board-roster /app/work/los-rays /app/work/fog-mask /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-playfield.sh \
    && cargo build --release --locked \
    && cp /app/target/release/fogpf /app/bin/fogpf

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
