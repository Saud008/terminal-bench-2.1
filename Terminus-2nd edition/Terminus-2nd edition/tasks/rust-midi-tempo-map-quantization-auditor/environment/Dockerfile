FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="rust-midi-tempo-map-quantization-auditor" \
      org.opencontainers.image.description="Rhythm chart playfield playtest verifier environment" \
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
COPY bline_mf ./bline_mf
COPY bline_pl ./bline_pl
COPY bline_wc ./bline_wc
COPY bline_tm ./bline_tm
COPY bline_qn ./bline_qn
COPY bline_lg ./bline_lg
COPY bline_ex ./bline_ex
COPY harmony_decoy ./harmony_decoy
COPY model ./model
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/midgrid

RUN mkdir -p /app/state/chart-manifest /app/work/tempo-ledger /app/work/beat-grid-ledger /app/work/lane-note-ledger /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh \
    && cargo generate-lockfile \
    && cargo build --release --locked \
    && cp /app/target/release/midgrid /app/bin/midgrid

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
