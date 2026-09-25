FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    coreutils \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
    asciinema \
 && rm -rf /var/lib/apt/lists/* \
 && command -v tmux >/dev/null \
 && command -v asciinema >/dev/null

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md

# Generate bundled fixtures at build time; remove the generator so agents cannot read it.
COPY tools/gen_fixtures.py /app/tools/gen_fixtures.py
RUN python3 /app/tools/gen_fixtures.py \
 && rm -f /app/tools/gen_fixtures.py \
 && rmdir /app/tools 2>/dev/null || true \
 && sed -i 's/\r$//' /app/bin/amavis-quarantine /app/scripts/*.sh /app/lib/*.sh /app/lib/decoy/*.sh \
 && chmod +x /app/bin/amavis-quarantine /app/scripts/*.sh /app/lib/*.sh /app/lib/decoy/*.sh \
 && mkdir -p /app/output /app/work/spool/spam /app/work/spool/virus /app/work/released/spam /app/work/released/virus /app/state \
 && bash /app/scripts/reset-state.sh
