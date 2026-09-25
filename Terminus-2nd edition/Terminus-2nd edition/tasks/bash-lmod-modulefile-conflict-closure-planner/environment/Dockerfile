FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tmux \
    asciinema \
    python3 \
    python3-venv \
    make \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv
RUN /opt/verifier-venv/bin/pip install --no-cache-dir \
    pytest==9.0.3 \
    pytest-json-ctrf==0.5.0

ENV PATH=/opt/verifier-venv/bin:/opt/verifier-scripts:/app/sbin:${PATH}

COPY verifier-scripts/rebuild-lmodplan /opt/verifier-scripts/rebuild-lmodplan
RUN chmod +x /opt/verifier-scripts/rebuild-lmodplan

COPY sbin /app/sbin/
COPY lib /app/lib/
COPY docs /app/docs/
COPY fixtures /app/fixtures/
COPY Makefile /app/Makefile
RUN chmod +x /app/sbin/lmodplan /app/lib/common/*.sh /app/lib/ingest/*.sh /app/lib/resolve/*.sh /app/lib/export/*.sh /app/lib/decoy/*.sh
RUN mkdir -p /app/state /app/output

COPY verifier-fixtures /opt/verifier-fixtures

CMD ["bash", "-lc", "echo Environment ready"]
