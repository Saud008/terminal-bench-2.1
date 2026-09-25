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

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

WORKDIR /app
COPY go.mod ./
RUN go mod tidy && go mod download

COPY config/ /app/config/
COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md
COPY verifier-fixtures/ /opt/verifier-fixtures/
COPY verifier-scripts/reference_cadence.py /opt/verifier-scripts/reference_cadence.py

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && bash /app/scripts/reset-state.sh \
    && go build -mod=readonly -o /usr/local/bin/cadence-replay ./cmd/cadence-replay \
    && chmod -R 750 /opt/verifier-fixtures \
    && chmod 755 /opt/verifier-scripts
