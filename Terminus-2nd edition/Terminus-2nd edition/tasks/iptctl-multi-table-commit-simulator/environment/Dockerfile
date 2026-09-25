FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    bash \
    ca-certificates \
    coreutils \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

WORKDIR /app
COPY tools/ /app/tools/
RUN python3 /app/tools/gen_fixtures.py
COPY scripts/ /app/scripts/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY decoy/ /app/decoy/
COPY opt-verifier-fixtures/ /opt/verifier-fixtures/
COPY README.md /app/README.md

RUN sed -i 's/\r$//' /app/scripts/iptctl /app/scripts/*.sh /app/lib/*.sh /app/tools/simulate.py /app/decoy/*.sh \
 && chmod +x /app/scripts/iptctl /app/scripts/*.sh /app/lib/*.sh /app/tools/simulate.py /app/decoy/*.sh \
 && install -m 0755 /app/scripts/iptctl /usr/local/bin/iptctl \
 && mkdir -p /app/output /app/state/work \
 && /app/scripts/reset-state.sh
