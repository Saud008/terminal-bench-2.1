FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

WORKDIR /app

COPY go.mod go.sum* ./
RUN touch go.sum \
    && go mod download || true

COPY cmd/ cmd/
COPY cipkernel/ cipkernel/
COPY docs/ docs/
COPY config/ config/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md ./

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-state.sh \
    && mkdir -p /app/output /app/state/slsacip \
    && go build -mod=mod -o /usr/local/bin/slsacip ./cmd/slsacip \
    && mkdir -p /opt/verifier-slsacip \
    && cp /app/config/slsacip.json /opt/verifier-slsacip/slsacip.json \
    && chmod a-w /opt/verifier-slsacip/slsacip.json
