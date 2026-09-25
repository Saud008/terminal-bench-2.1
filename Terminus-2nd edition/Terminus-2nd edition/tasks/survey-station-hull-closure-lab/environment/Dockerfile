FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="survey-station-hull-closure-lab" \
      org.opencontainers.image.description="Survey triangulation residual closure verifier environment" \
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
COPY station_bundle ./station_bundle
COPY geoid_shift ./geoid_shift
COPY micro_quant ./micro_quant
COPY antimeridian_cut ./antimeridian_cut
COPY overlap_veto ./overlap_veto
COPY campaign_lattice ./campaign_lattice
COPY geohull_rows ./geohull_rows
COPY seal_digest ./seal_digest
COPY atlas_write ./atlas_write
COPY decoy ./decoy
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/stationclos

ENV TB3_MICRO_SCALE=10000

RUN python3 /app/fixtures/build_fixtures.py --out-dir /app/fixtures/campaigns \
    && mkdir -p /app/work/station-hulls /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh \
    && cargo build --release --locked \
    && cp /app/target/release/stationclos /app/bin/stationclos

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
