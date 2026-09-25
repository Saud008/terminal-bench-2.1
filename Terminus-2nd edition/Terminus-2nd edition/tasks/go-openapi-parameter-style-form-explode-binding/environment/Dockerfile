FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/verifier-venv

COPY requirements.txt /tmp/requirements.txt
RUN /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV GOFLAGS=-mod=readonly
ENV CGO_ENABLED=0
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ cmd/
COPY internal/ internal/
COPY docs/ docs/
COPY config/ config/
COPY fixtures/ fixtures/
COPY hidden-fixtures/ /opt/verifier-fixtures/
COPY scripts/ scripts/
COPY README.md ./

RUN mkdir -p /app/output /app/state /logs/verifier \
    && chmod +x /app/scripts/reset-state.sh /app/scripts/start-server.sh /app/scripts/verifier-rebuild.sh \
    && find /app/fixtures -type f \( -name '*.yaml' -o -name '*.json' \) -exec sed -i 's/\r$//' {} + \
    && go build -mod=readonly -o /usr/local/bin/paramgate ./cmd/paramgate
