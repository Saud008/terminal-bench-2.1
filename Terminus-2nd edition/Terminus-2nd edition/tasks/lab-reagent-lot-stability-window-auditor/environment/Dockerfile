FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="lab-reagent-lot-stability-window-auditor" \
      org.opencontainers.image.description="Lab reagent stability correlation closure verifier environment" \
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
COPY session_io ./session_io
COPY provenance_digest ./provenance_digest
COPY chrono_integral ./chrono_integral
COPY assay_coupling ./assay_coupling
COPY calendar_extend ./calendar_extend
COPY closure_rank ./closure_rank
COPY correlation_store ./correlation_store
COPY closure_emit ./closure_emit
COPY decoy ./decoy
COPY protocol ./protocol
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/reagentwin

RUN python3 /app/fixtures/build_fixtures.py --seed 7719 --out-dir /app/fixtures/lab_sessions \
    && mkdir -p /app/work/stability-correlation /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh \
    && cargo build --release \
    && cp /app/target/release/reagentwin /app/bin/reagentwin

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
