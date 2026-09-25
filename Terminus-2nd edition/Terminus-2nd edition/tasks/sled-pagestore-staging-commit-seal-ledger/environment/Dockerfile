FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
    asciinema \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock \
 && rm -f /tmp/requirements.lock

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/app/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
ENV PYTHONPATH="/app/lib"

WORKDIR /app

COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY hidden/ /opt/verifier-fixtures/
COPY README.md /app/README.md

RUN mkdir -p /app/bin /app/state /app/state/pins /app/output /logs/verifier \
 && find /app/scripts /app/lib -type f \( -name '*.sh' -o -name 'sledtool' -o -name '*.py' \) -exec sed -i 's/\r$//' {} + \
 && chmod +x /app/scripts/*.sh /app/scripts/sledtool \
 && install -m 0755 /app/scripts/sledtool /app/bin/sledtool \
 && install -m 0755 /app/bin/sledtool /usr/local/bin/sledtool \
 && bash /app/scripts/reset-state.sh
