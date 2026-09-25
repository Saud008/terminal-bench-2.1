FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

LABEL org.opencontainers.image.title="radio-spectrum-license-coverage-catalog" \
      org.opencontainers.image.description="RF license atlas builder verifier environment" \
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
COPY fixtures/bundles /opt/rflicat-bundles/bundles
COPY fixtures/seeds.json /opt/rflicat-bundles/seeds.json
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/rflicat

RUN mkdir -p /app/state /app/work /app/output /app/bin \
    && chmod a-w /opt/rflicat-bundles/seeds.json /opt/rflicat-bundles/bundles/*.json \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-state.sh \
    && cargo build --release --locked \
    && cp /app/target/release/rflicat /app/bin/rflicat

ENV PATH="/app/bin:/usr/local/cargo/bin:${PATH}"
