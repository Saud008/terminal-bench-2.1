FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="clinical-trial-randomization-balance-monitor" \
      org.opencontainers.image.description="Clinical trial randomization balance monitor verifier environment" \
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
COPY manifest ./manifest
COPY alpha ./alpha
COPY stratify ./stratify
COPY blocks ./blocks
COPY ceilings ./ceilings
COPY closure ./closure
COPY ledger ./ledger
COPY pipeline ./pipeline
COPY decoy ./decoy
COPY docs ./docs
COPY fixtures ./fixtures
COPY config ./config
COPY scripts ./scripts

RUN mkdir -p /app/state /app/work /app/output /app/bin \
    && cargo build --release --locked \
    && cp /app/target/release/rtbalctl /app/bin/rtbalctl

ENV PATH="/app/bin:${PATH}"
