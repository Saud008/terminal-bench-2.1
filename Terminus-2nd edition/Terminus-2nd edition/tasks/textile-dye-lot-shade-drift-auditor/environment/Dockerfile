FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.title="textile-dye-lot-shade-drift-auditor" \
      org.opencontainers.image.description="Textile dye-lot shade drift Bash AWK auditor" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv tmux asciinema jq gawk \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
       pytest==9.0.3 pytest-json-ctrf==0.5.0

COPY lib ./lib
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/shadedrift

RUN mkdir -p /app/state/shade-correlation /app/work /app/output /app/bin \
    && ln -sf /app/scripts/shadedrift /app/bin/shadedrift \
    && find /app/lib/shadeaudit -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && find /app/lib/shadeaudit -name '*.sh' -exec chmod +x {} + \
    && chmod +x /app/scripts/shadedrift /app/scripts/reset-state.sh /app/scripts/rebuild-shadedrift.sh

ENV PATH="/app/bin:/opt/verifier-venv/bin:${PATH}"
