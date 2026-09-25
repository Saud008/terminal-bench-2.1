FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="desalination-membrane-fouling-trend-profiler" \
      org.opencontainers.image.description="Desalination membrane fouling trend chronicle verifier environment" \
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
COPY d9_r8load ./d9_r8load
COPY d9_f1bind ./d9_f1bind
COPY d9_p3norm ./d9_p3norm
COPY d9_c5anchor ./d9_c5anchor
COPY d9_m2lineage ./d9_m2lineage
COPY d9_g4bridge ./d9_g4bridge
COPY d9_s6trend ./d9_s6trend
COPY d9_l7emit ./d9_l7emit
COPY grade_decoy ./grade_decoy
COPY schema ./schema
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY support ./support
COPY hidden /opt/verifier-fixtures/rotrace

RUN mkdir -p /app/state/pressure-buffer /app/work/cleaning-buffer /app/work/ndp-grid /app/work/trend-scratch /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh \
    && cargo build --release --locked \
    && cp /app/target/release/rotrace /app/bin/rotrace

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
