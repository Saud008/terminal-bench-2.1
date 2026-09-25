FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

# Dependency installs + agent user before any source COPY (cache-stable layer).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        patch \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash agent \
    && python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==8.4.1 \
        pytest-json-ctrf==0.3.5 \
    && mkdir -p /home/agent/.cache/go-build /logs/verifier \
    && chown agent:agent /home/agent/.cache /home/agent/.cache/go-build \
    && chmod 700 /logs/verifier

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CGO_ENABLED=0
ENV GOCACHE=/home/agent/.cache/go-build

WORKDIR /app
COPY --chown=agent:agent go.mod ./
COPY --chown=agent:agent cmd ./cmd
COPY --chown=agent:agent internal ./internal
COPY --chown=agent:agent docs ./docs
COPY --chown=agent:agent fixtures ./fixtures
COPY --chown=agent:agent scripts ./scripts
COPY hidden /opt/verifier-fixtures/iceexpctl

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/reset-state.sh /app/scripts/verifier-rebuild.sh \
    && mkdir -p /app/state /app/work /app/output /app/bin \
    && chown agent:agent /app /app/state /app/work /app/output /app/bin \
    && runuser -u agent -- python3 /app/fixtures/build_fixtures.py \
    && ICEEXP_HIDDEN_ROOT=/opt/verifier-fixtures/iceexpctl python3 /app/fixtures/build_fixtures.py \
    && runuser -u agent -- go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/iceexpctl ./cmd/iceexpctl
# No final USER directive: Harbor runs agent as user=agent and verifier as root.
# /opt/verifier-venv and /opt/verifier-fixtures stay root-owned (default); agent cannot overwrite them.
