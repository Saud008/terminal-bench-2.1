FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

LABEL org.opencontainers.image.title="bgp-routeleak-risk-calibration-lab" \
      org.opencontainers.image.description="BGP route-leak risk calibration and eval lab" \
      org.opencontainers.image.vendor="anonymous"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tmux asciinema ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
       pytest==9.0.3 pytest-json-ctrf==0.5.0

COPY routeleak_lab ./routeleak_lab
COPY support ./support
COPY config ./config
COPY docs ./docs
COPY tools ./tools
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden/experiments /opt/verifier-fixtures/routeleaklab/experiments

RUN mkdir -p /app/state /app/output /app/bin \
    && find /app/scripts -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/*.sh \
    && printf '%s\n' '#!/usr/bin/env bash' 'export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"' 'exec python3 -m routeleak_lab "$@"' > /usr/local/bin/routeleaklab \
    && chmod +x /usr/local/bin/routeleaklab

ENV PATH="/usr/local/bin:/opt/verifier-venv/bin:${PATH}"
ENV PYTHONPATH="/app"
