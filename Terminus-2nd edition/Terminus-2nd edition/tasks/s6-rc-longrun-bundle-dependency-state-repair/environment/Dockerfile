FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema \
        ca-certificates \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY tools/ /app/tools/
COPY scripts/ /app/scripts/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY README.md /app/README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh /app/lib/*.sh /app/bin/s6-bundle-resolver \
    && chmod +x /app/scripts/*.sh /app/lib/*.sh /app/bin/s6-bundle-resolver \
    && chmod +x /app/tools/bundle_parser.py /app/tools/s6_rc_mock.py \
    && mkdir -p /app/output /app/state/rc \
    && : > /app/output/.parser-touch
