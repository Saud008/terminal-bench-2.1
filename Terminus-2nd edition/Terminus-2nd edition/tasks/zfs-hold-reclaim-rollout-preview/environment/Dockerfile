FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.title="zfs-hold-reclaim-rollout-preview" \
      org.opencontainers.image.description="ZFS hold reclaim rollout preview verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv tmux asciinema jq coreutils patch \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
       pytest==9.0.3 pytest-json-ctrf==0.5.0

COPY internal ./internal
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden/scenarios /opt/verifier-fixtures/zfshold

RUN mkdir -p /app/state /app/work /app/output /app/bin \
    && ln -sf /app/scripts/zfshold /app/bin/zfshold \
    && find /app/internal/zfsroll -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && find /app/internal/zfsroll -name '*.sh' -exec chmod +x {} + \
    && chmod +x /app/scripts/zfshold /app/scripts/reset-state.sh /app/scripts/rebuild-zfshold.sh

ENV PATH="/app/bin:/opt/verifier-venv/bin:${PATH}"
