FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="cement-kiln-energy-balance-profiler" \
      org.opencontainers.image.description="Cement kiln heat balance ledger profiler verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

# Agent rebuilds kilnbal at verify time; single-stage Rust image is intentional.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip tmux asciinema \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir --break-system-packages \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0 \
    && mkdir -p /app/state/tele-buffer /app/work/fuel-buffer /app/work/probe-grid \
        /app/work/balance-scratch /app/output /app/bin

COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY c7_u9norm ./c7_u9norm
COPY c7_p4bias ./c7_p4bias
COPY c7_f2bind ./c7_f2bind
COPY c7_g5span ./c7_g5span
COPY c7_h3score ./c7_h3score
COPY c7_l8emit ./c7_l8emit
COPY grade_decoy ./grade_decoy
COPY c7_f6rows ./c7_f6rows
COPY c7_t6rows ./c7_t6rows
COPY schema ./schema
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY support ./support
COPY hidden /opt/verifier-fixtures/kilnbal

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-workspace.sh \
    && cargo build --release --locked \
    && cp /app/target/release/kilnbal /app/bin/kilnbal

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
