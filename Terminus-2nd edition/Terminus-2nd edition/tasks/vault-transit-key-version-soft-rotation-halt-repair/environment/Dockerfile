FROM --platform=linux/amd64 public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        curl \
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

WORKDIR /app

COPY go.mod ./
RUN go mod download

COPY cmd/ cmd/
COPY internal/ internal/
COPY docs/ docs/
COPY scripts/ scripts/
COPY README.md ./

RUN python3 /app/scripts/gen-fixtures.py \
    && mkdir -p /opt/verifier-fixtures \
    && cp -a /app/fixtures/policies /opt/verifier-fixtures/ \
    && (cd /opt/verifier-fixtures/policies && sha256sum *.json > /opt/verifier-fixtures/policies.sha256) \
    && chmod a-w /opt/verifier-fixtures/policies/*.json \
    && chmod a-w /opt/verifier-fixtures/policies.sha256 \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output /app/fixtures/policies \
    && go build -mod=readonly -o /usr/local/bin/transit-mock ./cmd/transit-mock
