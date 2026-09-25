FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    make \
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

ENV PATH="/opt/verifier-venv/bin:/app/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
ENV PYTHONPATH="/app/lib:${PYTHONPATH}"

WORKDIR /app

COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY docs/ /opt/verifier-contract-docs/
COPY fixtures/ /app/fixtures/
COPY fixtures/ /opt/verifier-fixtures/
COPY scripts/ /app/scripts/
COPY Makefile /app/Makefile
COPY README.md /app/README.md

RUN mkdir -p /app/bin /app/output /logs/verifier \
 && find /app/scripts /app/lib -type f \( -name '*.sh' -o -name 'atlasd' -o -name '*.py' \) -exec sed -i 's/\r$//' {} + \
 && chmod +x /app/scripts/*.sh /app/scripts/atlasd \
 && install -m 0755 /app/scripts/atlasd /app/bin/atlasd \
 && find /opt/verifier-fixtures /opt/verifier-contract-docs -type f -exec chmod a-w {} + \
 && bash /app/scripts/reset-state.sh
