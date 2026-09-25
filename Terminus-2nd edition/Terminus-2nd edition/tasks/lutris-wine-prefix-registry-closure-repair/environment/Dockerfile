FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
        asciinema \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && command -v tmux >/dev/null \
    && command -v asciinema >/dev/null

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin"

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY config/ /app/config/
COPY scripts/ /app/scripts/
COPY prefixes/ /app/prefixes/
COPY README.md /app/README.md

RUN sed -i 's/\r$//' /app/bin/lutris-resolve /app/scripts/*.sh /app/lib/*.sh \
    && chmod +x /app/bin/lutris-resolve /app/scripts/*.sh \
    && install -m 0755 /app/bin/lutris-resolve /usr/local/bin/lutris-resolve \
    && mkdir -p /app/output /app/prefixes/canonical/stellaris \
    && ln -sfn ../canonical/stellaris /app/prefixes/active/stellaris \
    && bash /app/scripts/reset-state.sh
