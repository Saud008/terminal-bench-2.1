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

RUN chmod +x /app/bin/tf-tag-sentinel /app/scripts/*.sh /app/lib/*.sh /app/lib/decoy/*.sh /app/lib/export/*.sh /app/stage/*.sh /app/tools/*.sh \
    && python3 /app/tools/build_fixtures.py \
    && mkdir -p /app/output /app/state /opt/verifier-fixtures/tf-plans /opt/verifier-fixtures/tf-policies /opt/verifier-broken-sentinel \
    && cp /app/tb3-bundle/tb3-random-plan.json /opt/verifier-fixtures/tf-plans/tb3-random-plan.json \
    && cp /app/tb3-bundle/tb3-random-policy.json /opt/verifier-fixtures/tf-policies/tb3-random-policy.json \
    && cp /app/tb3-bundle/tb3-meta.json /opt/verifier-fixtures/tf-plans/tb3-meta.json \
    && cp /app/lib/common.sh /opt/verifier-broken-sentinel/common.sh \
    && cp /app/lib/parse_plan.sh /opt/verifier-broken-sentinel/parse_plan.sh \
    && cp /app/lib/alias.sh /opt/verifier-broken-sentinel/alias.sh \
    && cp /app/lib/inherit.sh /opt/verifier-broken-sentinel/inherit.sh \
    && cp /app/lib/moved.sh /opt/verifier-broken-sentinel/moved.sh \
    && cp /app/lib/unknowns.sh /opt/verifier-broken-sentinel/unknowns.sh \
    && cp /app/lib/policy.sh /opt/verifier-broken-sentinel/policy.sh \
    && cp /app/lib/staging.sh /opt/verifier-broken-sentinel/staging.sh \
    && cp /app/lib/report.sh /opt/verifier-broken-sentinel/report.sh \
    && /app/tools/init_state.sh

ENV PATH="/app/bin:/opt/verifier-venv/bin:${PATH}"
