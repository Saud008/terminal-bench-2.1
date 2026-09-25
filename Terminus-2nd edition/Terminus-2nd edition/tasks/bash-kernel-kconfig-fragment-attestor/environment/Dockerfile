FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.title="bash-kernel-kconfig-fragment-attestor" \
      org.opencontainers.image.description="Kernel kconfig fragment merge attestor verifier environment" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv tmux asciinema jq \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

COPY tools ./tools
COPY lib ./lib
COPY config ./config
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/kcfg

RUN mkdir -p /app/state /app/work /app/output /app/bin \
    && ln -sf /app/scripts/kcfgattest /app/bin/kcfgattest \
    && find /app/lib -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && find /app/lib -name '*.sh' -exec chmod +x {} + \
    && sed -i 's/\r$//' /app/scripts/kcfgattest /app/scripts/reset-state.sh /app/scripts/rebuild-kcfgattest.sh \
    && chmod +x /app/scripts/kcfgattest /app/scripts/reset-state.sh /app/scripts/rebuild-kcfgattest.sh

ENV PATH="/app/bin:/opt/verifier-venv/bin:${PATH}"
