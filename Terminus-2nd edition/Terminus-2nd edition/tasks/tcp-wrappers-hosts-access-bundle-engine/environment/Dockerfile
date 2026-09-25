FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
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

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY internal/ /app/internal/
COPY tools/ /app/tools/
COPY opt-verifier-fixtures/ /opt/verifier-fixtures/
COPY README.md /app/README.md

RUN mkdir -p /app/output /app/work \
 && sed -i 's/\r$//' /app/bin/hostsctl /app/scripts/*.sh /app/lib/*.sh /app/lib/decoy/*.sh \
 && chmod +x /app/bin/hostsctl /app/scripts/*.sh /app/lib/*.sh /app/lib/decoy/*.sh \
 && install -m 0755 /app/bin/hostsctl /usr/local/bin/hostsctl \
 && bash /app/scripts/gen-fixtures.sh \
 && bash /app/scripts/reset-state.sh

LABEL org.opencontainers.image.source="terminus/tasks/tcp-wrappers-hosts-access-bundle-engine"
LABEL org.opencontainers.image.revision="1.0.0"
LABEL org.opencontainers.image.created="2026-06-27T00:00:00Z"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"
