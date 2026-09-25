FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
COPY wheels/ /tmp/wheels/
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --no-index --find-links /tmp/wheels --require-hashes -r /tmp/requirements.txt \
    && rm -rf /tmp/requirements.txt /tmp/wheels

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY stubs/ /app/stubs/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md

RUN mkdir -p /app/output /app/work \
    && sed -i 's/\r$//' /app/bin/pamreplay /app/scripts/*.sh /app/lib/*.sh /app/stubs/*.sh \
    && chmod +x /app/bin/pamreplay /app/scripts/*.sh /app/lib/*.sh /app/stubs/*.sh \
    && python3 /app/scripts/gen_manifest.py \
    && mkdir -p /opt/verifier-broken-pam \
    && cp -a /app/lib /opt/verifier-broken-pam/lib \
    && bash /app/scripts/reset-state.sh
