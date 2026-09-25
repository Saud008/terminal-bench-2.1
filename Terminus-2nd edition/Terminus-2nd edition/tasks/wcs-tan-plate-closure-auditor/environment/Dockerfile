FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

LABEL org.opencontainers.image.title="wcs-tan-plate-closure-auditor" \
      org.opencontainers.image.description="TAN plate-solution laboratory closure verifier environment" \
      org.opencontainers.image.vendor="anonymous"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        patch \
        python3 \
        python3-pip \
        python3-venv \
        sqlite3 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY verifier-requirements.txt /tmp/verifier-requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        -r /tmp/verifier-requirements.txt \
    && rm -f /tmp/verifier-requirements.txt

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CGO_ENABLED=0

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY cmd ./cmd
COPY internal ./internal
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY support ./support
COPY hidden /opt/verifier-fixtures/platclosectl

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/reset-state.sh /app/scripts/rebuild-platclosectl.sh \
    && mkdir -p /app/state /app/work/residual-matrix /app/output /app/bin \
    && printf '%s\n' '{"bind_pass":0}' > /app/state/bind-pass.json \
    && go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/platclosectl ./cmd/platclosectl
