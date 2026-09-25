FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        ca-certificates \
        coreutils \
        findutils \
        jq \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY scripts/ /app/scripts/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY config/ /app/config/
COPY README.md /app/README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh /app/lib/ebuild-phase/*.sh /app/bin/ebuild-phase \
    && chmod +x /app/scripts/*.sh /app/lib/ebuild-phase/*.sh /app/bin/ebuild-phase \
    && chmod +x /app/fixtures/*/files/bin/* 2>/dev/null || true \
    && mkdir -p /app/output /app/state /app/work
