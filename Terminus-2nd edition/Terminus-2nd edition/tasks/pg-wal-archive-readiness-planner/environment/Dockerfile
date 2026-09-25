FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        findutils \
        coreutils \
        gawk \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

WORKDIR /app
COPY bin/ /app/bin/
COPY scripts/ /app/scripts/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY tools/ /app/tools/

RUN chmod +x /app/bin/walplan /app/scripts/*.sh /app/lib/*.sh /app/lib/decoy/*.sh /app/lib/ingest/*.sh /app/lib/export/*.sh /app/tools/*.sh \
    && python3 /app/tools/build_fixtures.py \
    && mkdir -p /app/output /app/state /opt/verifier-fixtures/wal-archives /opt/verifier-fixtures/wal-config /opt/verifier-broken-walplan \
    && cp -r /app/tb3-bundle/tb3-random-timeline /opt/verifier-fixtures/wal-archives/tb3-random-timeline \
    && cp /app/tb3-bundle/tb3-clock.json /opt/verifier-fixtures/wal-config/segment-clock.json \
    && cp /app/lib/wal_name.sh /opt/verifier-broken-walplan/wal_name.sh \
    && cp /app/lib/timeline.sh /opt/verifier-broken-walplan/timeline.sh \
    && cp /app/lib/continuity.sh /opt/verifier-broken-walplan/continuity.sh \
    && cp /app/lib/partial.sh /opt/verifier-broken-walplan/partial.sh \
    && cp /app/lib/label.sh /opt/verifier-broken-walplan/label.sh \
    && cp /app/lib/target.sh /opt/verifier-broken-walplan/target.sh \
    && cp /app/lib/digest.sh /opt/verifier-broken-walplan/digest.sh \
    && cp /app/lib/staging.sh /opt/verifier-broken-walplan/staging.sh \
    && cp /app/lib/plan.sh /opt/verifier-broken-walplan/plan.sh \
    && /app/tools/init_state.sh

ENV PATH="/app/bin:/opt/verifier-venv/bin:${PATH}"
