FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="mining-blast-vibration-compliance-map" \
      org.opencontainers.image.description="Mining blast vibration compliance atlas verifier environment" \
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
COPY mbvcm_r01 ./mbvcm_r01
COPY mbvcm_r02 ./mbvcm_r02
COPY mbvcm_r03 ./mbvcm_r03
COPY mbvcm_r04 ./mbvcm_r04
COPY mbvcm_r05 ./mbvcm_r05
COPY mbvcm_r06 ./mbvcm_r06
COPY mbvcm_r07 ./mbvcm_r07
COPY mbvcm_r08 ./mbvcm_r08
COPY waveform_decoy ./waveform_decoy
COPY model ./model
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/seismocomply

RUN mkdir -p /app/state /app/work /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/clear-seismo-run.sh \
    && cargo build --release --locked \
    && cp /app/target/release/seismocomply /app/bin/seismocomply

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
