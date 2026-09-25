FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

COPY requirements.txt /tmp/requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
        psmisc \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CGO_ENABLED=0

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
COPY config/ /app/config/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY seed-vault/ /opt/verifier-fixtures/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-state.sh /app/scripts/verifier-rebuild.sh \
    && mkdir -p /app/output /app/work /app/state /opt/verifier-broken-livattest \
    && cp /app/internal/policy/continuity_gate.go /opt/verifier-broken-livattest/continuity_gate.go \
    && cp /app/internal/vault/trust_bind.go /opt/verifier-broken-livattest/trust_bind.go \
    && cp /app/internal/seal/ban_revoke.go /opt/verifier-broken-livattest/ban_revoke.go \
    && cp /app/internal/witness/chain_write.go /opt/verifier-broken-livattest/chain_write.go \
    && cp /app/internal/export/digest_emit.go /opt/verifier-broken-livattest/digest_emit.go \
    && cp /app/internal/clock/pin_clock.go /opt/verifier-broken-livattest/pin_clock.go \
    && go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/livattest ./cmd/livattest
