FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="rust-cranelift-ir-register-pressure-atlas" \
      org.opencontainers.image.description="Neutron flux residual occupancy verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip tmux asciinema patch \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5

COPY Cargo.toml Cargo.lock ./
COPY build.rs ./
COPY src ./src
COPY protocol ./protocol
COPY campaign_io ./campaign_io
COPY residual_kernel ./residual_kernel
COPY quantize ./quantize
COPY energy_order ./energy_order
COPY coincidence_veto ./coincidence_veto
COPY occupancy_scan ./occupancy_scan
COPY fluence_ledger ./fluence_ledger
COPY closure_rank ./closure_rank
COPY digest_line ./digest_line
COPY closure_emit ./closure_emit
COPY decoy ./decoy
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/fluxpress

ENV TB3_MICRON_EV_SCALE=1000

RUN python3 /app/fixtures/build_fixtures.py --out-dir /app/fixtures/rings \
    && mkdir -p /app/scratch/ring-fluence /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh \
    && cargo build --release --locked \
    && cp /app/target/release/fluxpress /app/bin/fluxpress

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
