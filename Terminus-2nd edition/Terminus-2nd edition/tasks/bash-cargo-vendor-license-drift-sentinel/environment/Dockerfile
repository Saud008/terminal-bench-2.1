FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    bash \
    coreutils \
    gawk \
    ca-certificates \
    python3 \
    python3-venv \
    tmux \
    asciinema \
 && rm -rf /var/lib/apt/lists/* \
 && command -v tmux >/dev/null \
 && command -v asciinema >/dev/null

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"

WORKDIR /app

COPY lib/ /app/lib/
COPY audit/ /app/audit/
COPY docs/ /app/docs/
COPY config/ /app/config/
COPY scripts/ /app/scripts/
COPY decoy/ /app/decoy/
COPY catalog/ /app/catalog/
COPY tools/ /app/tools/
COPY README.md /app/README.md

RUN mkdir -p /app/stage/license-compliance /app/state /app/output /opt/verifier-fixtures \
 && sed -i 's/\r$//' /app/scripts/cvls-governor /app/scripts/*.sh /app/lib/*.sh /app/decoy/*.sh \
 && chmod +x /app/scripts/cvls-governor /app/scripts/*.sh /app/lib/*.sh /app/decoy/*.sh \
 && install -m 0755 /app/scripts/cvls-governor /usr/local/bin/cvls-governor \
 && python3 /app/tools/write_fixtures.py \
 && bash /app/scripts/reset-state.sh

LABEL org.opencontainers.image.source="terminus/tasks/bash-cargo-vendor-license-drift-sentinel"
LABEL org.opencontainers.image.revision="1.0.0"
LABEL org.opencontainers.image.created="2026-07-02T00:00:00Z"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"
