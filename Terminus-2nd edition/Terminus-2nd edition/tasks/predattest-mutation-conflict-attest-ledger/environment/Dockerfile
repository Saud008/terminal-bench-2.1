FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.title="predattest-mutation-conflict-attest-ledger" \
      org.opencontainers.image.description="wavehold mutation-wave rollout hold-preview verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv tmux asciinema jq coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
       pytest==9.0.3 pytest-json-ctrf==0.5.0

COPY lib ./lib
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts

RUN mkdir -p /app/state/wavehold/runs /app/work /app/output /app/bin \
    && find /app/scripts -type f -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/wavehold /app/scripts/reset-state.sh \
    && ln -sf /app/scripts/wavehold /app/bin/wavehold \
    && ln -sf /app/scripts/wavehold /usr/local/bin/wavehold

ENV PATH="/app/bin:/opt/verifier-venv/bin:${PATH}"
ENV PYTHONPATH="/app/lib"
