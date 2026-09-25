FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

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
 && /opt/verifier-venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV GOCACHE=/opt/gocache
ENV GOFLAGS=-mod=readonly
ENV CGO_ENABLED=0

RUN mkdir -p /opt/gocache

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ cmd/
COPY internal/ internal/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md ./

RUN find /app/fixtures /app/scripts -type f \( -name '*.json' -o -name '*.jsonl' -o -name '*.sh' \) -exec sed -i 's/\x0d$//' {} + \
 && chmod +x /app/scripts/*.sh \
 && mkdir -p /app/output /app/state /app/work \
 && go build -mod=readonly -o /usr/local/bin/dnsmasqledger ./cmd/dnsmasqledger \
 && bash /app/scripts/reset-state.sh
