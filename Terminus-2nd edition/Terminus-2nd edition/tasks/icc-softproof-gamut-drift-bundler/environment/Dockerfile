FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        bc \
        ca-certificates \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        jq \
        coreutils \
        findutils \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

WORKDIR /app
COPY bin/ /app/bin/
COPY scripts/ /app/scripts/
COPY lib/ /app/lib/
COPY stage/ /app/stage/
COPY docs/ /app/docs/
COPY config/ /app/config/
COPY fixtures/ /app/fixtures/
COPY tools/ /app/tools/

RUN chmod +x /app/bin/icc-drift-bundler /app/scripts/*.sh /app/lib/*.sh /app/lib/decoy/*.sh /app/stage/*.sh /app/tools/*.sh \
    && python3 /app/tools/build_fixtures.py \
    && mkdir -p /app/output /app/state /opt/verifier-fixtures/icc /opt/verifier-broken-icc \
    && cp /app/tb3-bundle/tb3-readings.tsv /opt/verifier-fixtures/icc/tb3-readings.tsv \
    && cp /app/tb3-bundle/tb3-profile.json /opt/verifier-fixtures/icc/tb3-profile.json \
    && cp /app/tb3-bundle/tb3-paper.json /opt/verifier-fixtures/icc/tb3-paper.json \
    && cp /app/tb3-bundle/tb3-tickets.json /opt/verifier-fixtures/icc/tb3-tickets.json \
    && cp /app/tb3-bundle/tb3-meta.json /opt/verifier-fixtures/icc/tb3-meta.json \
    && for f in common parse_readings lab_delta paper_lineage intent_policy profile_checksum ticket_epoch staging export_report; do \
         cp /app/lib/${f}.sh /opt/verifier-broken-icc/${f}.sh; \
       done \
    && /app/tools/init_state.sh

ENV PATH="/app/bin:/opt/verifier-venv/bin:${PATH}"
