FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        gawk \
        coreutils \
        findutils \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
        asciinema \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && command -v gawk >/dev/null \
    && command -v tmux >/dev/null \
    && command -v asciinema >/dev/null

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin"

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY config/ /app/config/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY merge/ /app/merge/
COPY stage/ /app/stage/
COPY tools/ /app/tools/
COPY wrap/ /app/wrap/
COPY verifier-fixtures/agg/ /opt/verifier-fixtures/agg/

RUN sed -i 's/\r$//' \
        /app/bin/agg-run \
        /app/scripts/*.sh \
        /app/merge/*.sh \
        /app/stage/*.sh \
        /app/tools/*.sh \
        /app/wrap/*.sh \
        /app/lib/*.awk \
    && chmod +x \
        /app/bin/agg-run \
        /app/scripts/*.sh \
        /app/merge/*.sh \
        /app/stage/*.sh \
        /app/tools/*.sh \
        /app/wrap/*.sh \
    && install -m 0755 /app/bin/agg-run /usr/local/bin/agg-run \
    && mkdir -p /app/output /app/state \
    && bash /app/scripts/reset-state.sh
