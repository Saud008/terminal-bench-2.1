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

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

WORKDIR /app

COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY docs/ /opt/verifier-contract-docs/
COPY fixtures/ /app/fixtures/
COPY fixtures/ /opt/verifier-fixtures/
COPY scripts/ /app/scripts/
COPY Makefile /app/Makefile
COPY README.md /app/README.md

RUN mkdir -p /app/bin \
 && find /app/scripts /app/lib/tscn -type f \( -name '*.sh' -o -name 'scenectl' \) -exec sed -i 's/\r$//' {} + \
 && chmod +x /app/scripts/*.sh /app/lib/tscn/*.sh /app/lib/tscn/decoy/*.sh /app/lib/tscn/_legacy/*.sh /app/lib/staging/*.sh /app/scripts/scenectl \
 && install -m 0755 /app/scripts/scenectl /app/bin/scenectl \
 && touch -d @1700000000 /app/fixtures/trees/village-remap/base/*.tscn \
    /app/fixtures/trees/orphan-trap/base/*.tscn \
    /app/fixtures/trees/cycle-trap/base/*.tscn \
    /app/fixtures/trees/crlf-trap/base/*.tscn \
    /app/fixtures/trees/texture-ring-trap/base/*.tscn \
 && touch -d @1700000100 /app/fixtures/trees/village-remap/left/*.tscn \
    /app/fixtures/trees/orphan-trap/left/*.tscn \
    /app/fixtures/trees/cycle-trap/left/*.tscn \
    /app/fixtures/trees/crlf-trap/left/*.tscn \
    /app/fixtures/trees/texture-ring-trap/left/*.tscn \
 && touch -d @1700000200 /app/fixtures/trees/village-remap/right/*.tscn \
    /app/fixtures/trees/orphan-trap/right/*.tscn \
    /app/fixtures/trees/cycle-trap/right/*.tscn \
    /app/fixtures/trees/crlf-trap/right/*.tscn \
    /app/fixtures/trees/texture-ring-trap/right/*.tscn \
 && find /opt/verifier-fixtures /opt/verifier-contract-docs -type f -exec chmod a-w {} + \
 && mkdir -p /app/output \
 && bash /app/scripts/reset-state.sh
