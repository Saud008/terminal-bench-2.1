FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="water-treatment-chemical-dose-auditor" \
      org.opencontainers.image.description="Water treatment chemical dose safety auditor verifier environment" \
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
COPY internal ./internal
COPY shift_io ./shift_io
COPY decoy ./decoy
COPY protocol ./protocol
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/wtcdctl

RUN python3 /app/fixtures/build_fixtures.py --seed 4821 --out-dir /app/fixtures/plant_shifts \
    && mkdir -p /app/work/dose-ledger /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh /app/scripts/rebuild-wtcdctl.sh \
    && cargo build --release \
    && cp /app/target/release/wtcdctl /app/bin/wtcdctl

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
