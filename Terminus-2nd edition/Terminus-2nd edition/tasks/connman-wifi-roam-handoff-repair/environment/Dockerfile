FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        python3 \
        python3-pip \
        python3-venv \
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
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY tools/ /app/tools/
COPY README.md /app/README.md

RUN python3 /app/tools/build-fixtures.py \
    && python3 /app/tools/build-hidden-fixtures.py \
    && mkdir -p /app/output /opt/verifier-broken-roam \
    && cp /app/lib/roam/fsm.sh /opt/verifier-broken-roam/ \
    && cp /app/lib/roam/scan_ledger.sh /opt/verifier-broken-roam/ \
    && cp /app/lib/roam/service_rank.sh /opt/verifier-broken-roam/ \
    && cp /app/lib/roam/consent.sh /opt/verifier-broken-roam/ \
    && cp /app/lib/roam/dhcp_hook.sh /opt/verifier-broken-roam/ \
    && find /app/scripts /app/lib -type f \( -name '*.sh' -o -name 'connman-roamctl' \) -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/connman-roamctl /app/scripts/*.sh /app/lib/roam/*.sh \
    && bash /app/scripts/reset-state.sh
