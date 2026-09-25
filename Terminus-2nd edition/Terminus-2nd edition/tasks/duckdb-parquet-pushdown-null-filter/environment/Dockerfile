FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV GOCACHE=/opt/gocache
ENV GOFLAGS=-mod=readonly

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ cmd/
COPY internal/ internal/
COPY docs/ docs/
COPY config/ config/
COPY fixtures/ fixtures/
COPY verifier-fixtures/ /opt/verifier-fixtures/
COPY scripts/ scripts/
COPY README.md ./

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-state.sh /app/scripts/build-cli.sh \
    && mkdir -p /app/output /app/state \
    && go build -mod=readonly -o /usr/local/bin/parquet-pushdown-scan ./cmd/parquet-pushdown-scan
