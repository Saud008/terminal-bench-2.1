FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        tmux \
        asciinema \
        jq \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && command -v tmux >/dev/null \
    && command -v asciinema >/dev/null

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

WORKDIR /app
COPY README.md /app/
COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY fixtures/ /opt/fixture-seed/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/

RUN sed -i 's/\r$//' /app/scripts/*.sh /app/lib/*.sh /app/bin/stage2-audit \
    && chmod +x /app/scripts/*.sh /app/lib/*.sh /app/bin/stage2-audit \
    && mkdir -p /app/output /app/state/mount-snapshots /app/state/mount-gate /app/state/stage2-staging
