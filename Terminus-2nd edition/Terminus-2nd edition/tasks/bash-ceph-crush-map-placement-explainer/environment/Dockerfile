FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.title="bash-ceph-crush-map-placement-explainer" \
      org.opencontainers.image.description="Ceph CRUSH placement trace explainer verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv tmux asciinema jq patch \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

COPY internal ./internal
COPY config ./config
COPY docs ./docs
COPY maps ./maps
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/crpe

RUN mkdir -p /app/state /app/work /app/output /app/bin \
    && ln -sf /app/scripts/crpe /app/bin/crpe \
    && find /app/internal/crpe91 -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && find /app/internal/crpe91 -name '*.sh' -exec chmod +x {} + \
    && chmod +x /app/scripts/crpe /app/scripts/reset-state.sh /app/scripts/rebuild-crpe.sh
