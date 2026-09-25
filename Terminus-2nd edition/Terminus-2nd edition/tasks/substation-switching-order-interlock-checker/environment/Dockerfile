FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="substation-switching-order-interlock-checker" \
      org.opencontainers.image.description="Substation switching interlock checker verifier environment" \
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
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/sublock

RUN mkdir -p /app/var/sub /app/output /app/bin \
    && sed -i 's/\r$//' /app/scripts/harness/*.sh /app/scripts/reset-state.sh \
    && chmod +x /app/scripts/harness/reset-state.sh /app/scripts/reset-state.sh \
    && cargo build --release --locked \
    && cp /app/target/release/relayctl /app/bin/relayctl

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
