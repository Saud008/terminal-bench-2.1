FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        coreutils \
        gawk \
        make \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY ingest/ /app/ingest/
COPY scripts/ /app/scripts/
COPY config/ /app/config/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY decoy/ /app/decoy/
COPY wrap/ /app/wrap/
COPY verifier-fixtures/workshop/ /opt/verifier-fixtures/workshop/

RUN find /app/lib /app/ingest -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && sed -i 's/\r$//' /app/scripts/*.sh /app/bin/workshop-plan \
    && chmod +x /app/bin/workshop-plan /app/scripts/*.sh \
    && find /app/lib /app/ingest -name '*.sh' -exec chmod +x {} \; \
    && mkdir -p /app/state /app/output \
    && bash /app/scripts/reset-state.sh

ENV PATH="/app/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
