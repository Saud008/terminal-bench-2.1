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

RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir \
    pytest==9.0.3 \
    pytest-json-ctrf==0.5.0

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV GOCACHE=/opt/gocache
ENV GOFLAGS=-mod=readonly

RUN mkdir -p /opt/gocache

WORKDIR /app
COPY go.mod go.sum ./
COPY cmd/ cmd/
COPY pkg/ pkg/
COPY contracts/ contracts/
COPY docs/ docs/
COPY tooling/ tooling/
COPY README.md ./
COPY corpus/ corpus/

RUN sed -i 's/\r$//' /app/tooling/*.sh \
 && chmod +x /app/tooling/*.sh \
 && go mod tidy \
 && go build -mod=readonly -o /usr/local/bin/wireclock ./cmd/wireclock \
 && bash /app/tooling/reset-state.sh

LABEL org.opencontainers.image.source="https://github.com/snorkel-ai/terminus"
LABEL org.opencontainers.image.revision="bson-objectid-clock-skew-duplicate-guard"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"
