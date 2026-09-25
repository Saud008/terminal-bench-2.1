FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.title="meilisearch-geo-bbox-filter-ranking-bundler" \
      org.opencontainers.image.description="Meilisearch geo filter playfield puzzle planner" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv tmux asciinema jq coreutils patch \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

COPY internal ./internal
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden/levels /opt/verifier-fixtures/geobox

RUN mkdir -p /app/state /app/work /app/output /app/bin \
    && ln -sf /app/scripts/geoboxplay /app/bin/geoboxplay \
    && ln -sf /app/scripts/rebuild-geoboxplay.sh /app/bin/rebuild-geoboxplay.sh \
    && find /app/internal/mbx7 -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && find /app/internal/mbx7 -name '*.sh' -exec chmod +x {} + \
    && chmod +x /app/scripts/geoboxplay /app/scripts/reset-state.sh /app/scripts/rebuild-geoboxplay.sh

ENV PATH="/app/bin:/opt/verifier-venv/bin:${PATH}"
