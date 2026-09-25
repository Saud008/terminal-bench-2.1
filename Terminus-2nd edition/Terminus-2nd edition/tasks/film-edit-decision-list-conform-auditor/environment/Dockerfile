FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    bash \
    coreutils \
    gawk \
    patch \
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
COPY catalog/ /app/catalog/
COPY config/ /app/config/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY decoy/ /app/decoy/
COPY wrap/ /app/wrap/
COPY opt-verifier-fixtures/ /opt/verifier-fixtures/
COPY README.md /app/README.md

RUN mkdir -p /app/state /app/output \
 && find /app/fixtures /opt/verifier-fixtures -type f \( -name '*.edl' -o -name '*.map' -o -name '*.txt' -o -name '*.json' \) -exec sed -i 's/\r$//' {} + \
 && sed -i 's/\r$//' /app/scripts/edl-conform-audit /app/scripts/*.sh /app/lib/*.sh /app/lib/*.awk /app/decoy/*.sh /app/catalog/*.sh /app/audit/*.sh \
 && chmod +x /app/scripts/edl-conform-audit /app/scripts/*.sh /app/lib/*.sh /app/decoy/*.sh /app/catalog/*.sh /app/audit/*.sh \
 && install -m 0755 /app/scripts/edl-conform-audit /usr/local/bin/edl-conform-audit \
 && bash /app/scripts/reset-state.sh

LABEL org.opencontainers.image.source="terminus/tasks/film-edit-decision-list-conform-auditor"
LABEL org.opencontainers.image.revision="1.0.0"
LABEL org.opencontainers.image.created="2026-07-08T00:00:00Z"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"
