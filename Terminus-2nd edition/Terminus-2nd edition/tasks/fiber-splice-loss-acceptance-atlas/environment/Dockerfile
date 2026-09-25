FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="fiber-splice-loss-acceptance-atlas" \
      org.opencontainers.image.description="Fiber splice loss acceptance atlas verifier environment" \
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
COPY bundle_latch ./bundle_latch
COPY morlet_scan ./morlet_scan
COPY hopf_fold ./hopf_fold
COPY route_weave ./route_weave
COPY junction_ledger ./junction_ledger
COPY atlas_emit ./atlas_emit
COPY tf_decoy ./tf_decoy
COPY tools ./tools
COPY model ./model
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/fsplatlas

RUN mkdir -p /app/state/capture-cache /app/work/reflection-buffer /app/work/topology-snapshot /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh \
    && cargo generate-lockfile \
    && cargo build --release --locked \
    && cp /app/target/release/fsplatlas /app/bin/fsplatlas

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
