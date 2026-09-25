FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.title="hci-bond-trust-reconnect-rollout-preview" \
      org.opencontainers.image.description="HCI bond-trust reconnect cutover rollout preview verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv tmux asciinema jq coreutils patch \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
       pytest==9.0.3 pytest-json-ctrf==0.5.0

COPY lib ./lib
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY overlay/scenarios /opt/verifier-fixtures/hciroll

RUN mkdir -p /app/state /app/work /app/output /app/bin \
    && ln -sf /app/scripts/hciroll /app/bin/hciroll \
    && find /app/lib/boltlane -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && find /app/lib/boltlane -name '*.sh' -exec chmod +x {} + \
    && chmod +x /app/scripts/hciroll /app/scripts/reset-state.sh /app/scripts/rebuild-hciroll.sh

ENV PATH="/app/bin:/opt/verifier-venv/bin:${PATH}"
