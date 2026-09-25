FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

COPY requirements.txt /tmp/requirements.txt
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
 && rm -rf /var/lib/apt/lists/* \
 && python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ENV CGO_ENABLED=0

WORKDIR /app
COPY go.mod /app/go.mod
COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
COPY docs/ /app/docs/
COPY tools/ /app/tools/
COPY scripts/ /app/scripts/
COPY trust/ /app/trust/
COPY README.md /app/README.md

RUN chmod +x /app/scripts/gen-fixtures.sh /app/scripts/reset-state.sh /app/scripts/rebuild-bundlectl.sh \
 && mkdir -p /app/output /app/state /opt/verifier-fixtures \
 && /app/scripts/gen-fixtures.sh \
 && rm -rf /app/verifier-fixtures
