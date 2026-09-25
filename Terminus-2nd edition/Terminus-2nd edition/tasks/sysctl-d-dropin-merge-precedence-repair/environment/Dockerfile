FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    bash python3 python3-venv python3-pip ca-certificates tmux asciinema findutils \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock \
 && rm -f /tmp/requirements.lock

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin"

WORKDIR /app
COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md

RUN mkdir -p /app/output \
 && sed -i 's/\r$//' /app/bin/sysctlmerge /app/scripts/*.sh /app/lib/*.sh \
 && chmod +x /app/bin/sysctlmerge /app/scripts/*.sh /app/lib/*.sh \
 && install -m 0755 /app/bin/sysctlmerge /usr/local/bin/sysctlmerge \
 && bash /app/scripts/reset-state.sh
