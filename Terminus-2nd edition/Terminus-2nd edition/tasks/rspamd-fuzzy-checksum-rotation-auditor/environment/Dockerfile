FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

LABEL org.opencontainers.image.title="rspamd-fuzzy-checksum-rotation-auditor"
LABEL org.opencontainers.image.description="Terminus task environment for rspamd fuzzy checksum rotation audit CLI"
LABEL org.opencontainers.image.source="terminus-tasks/rspamd-fuzzy-checksum-rotation-auditor"
LABEL org.opencontainers.image.version="2.0"
LABEL org.opencontainers.image.licenses="NOASSERTION"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        gawk \
        patch \
        python3 \
        python3-pip \
        python3-venv \
        sqlite3 \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

WORKDIR /app

COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY scripts/ /app/scripts/
COPY tools/ /app/tools/
COPY README.md /app/README.md

RUN install -D -m 0755 /app/scripts/rspamd-fuzzy-audit /app/bin/rspamd-fuzzy-audit \
    && python3 /app/tools/build-fixtures.py \
    && python3 /app/tools/build-hidden-fixtures.py \
    && mkdir -p /app/output /app/state \
    && find /app/bin /app/scripts /app/lib -type f \( -name '*.sh' -o -name 'rspamd-fuzzy-audit' -o -name '*.awk' \) | while read -r f; do \
         sed -i 's/\r$//' "$f" 2>/dev/null || true; \
       done \
    && chmod +x /app/bin/rspamd-fuzzy-audit /app/scripts/*.sh \
    && find /app/lib -name '*.sh' -exec chmod +x {} \; \
    && bash /app/scripts/reset-state.sh
