FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="lab-instrument-calibration-chain-dossier" \
      org.opencontainers.image.description="Lab instrument calibration chain dossier verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip tmux asciinema patch \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY Cargo.toml ./
COPY build.rs ./
COPY src ./src
COPY line_validity ./line_validity
COPY walk_parent ./walk_parent
COPY budget_rss ./budget_rss
COPY gate_operator ./gate_operator
COPY matrix_limits ./matrix_limits
COPY register_store ./register_store
COPY vault_snapshot ./vault_snapshot
COPY row_publish ./row_publish
COPY run_io ./run_io
COPY meter_parse ./meter_parse
COPY decoy ./decoy
COPY protocol ./protocol
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/calbind

RUN python3 /app/fixtures/build_fixtures.py --seed 8842 --out-dir /app/fixtures/cal_runs \
    && mkdir -p /app/state /app/work /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh \
    && cargo build --release \
    && cp /app/target/release/calbind /app/bin/calbind

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
