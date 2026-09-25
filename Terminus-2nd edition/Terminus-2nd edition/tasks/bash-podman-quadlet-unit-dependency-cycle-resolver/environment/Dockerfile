FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        ca-certificates \
        systemd \
        tmux \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY tools/ /app/tools/
COPY scripts/ /app/scripts/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY README.md /app/README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh /app/lib/*.sh /app/bin/quadlet-resolver \
    && chmod +x /app/scripts/*.sh /app/lib/*.sh /app/bin/quadlet-resolver \
    && chmod +x /app/tools/quadlet_parser.py \
    && mkdir -p /app/output \
    && : > /app/output/.parser-touch \
    && printf '#!/bin/sh\nexec /bin/true "$@"\n' > /usr/bin/podman \
    && chmod +x /usr/bin/podman
