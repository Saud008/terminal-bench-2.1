FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
        passwd \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash agent \
    && python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0 \
    && mkdir -p /home/agent/.cargo /logs/verifier \
    && chown -R agent:agent /home/agent \
    && chmod 700 /logs/verifier \
    && chmod -R a-w /opt/verifier-venv

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0
ENV CARGO_HOME=/usr/local/cargo

WORKDIR /app

COPY --chown=agent:agent Cargo.toml Cargo.lock README.md ./
COPY --chown=agent:agent .cargo/ .cargo/
COPY --chown=agent:agent vendor/ vendor/
COPY --chown=agent:agent crates/ crates/
COPY --chown=agent:agent docs/ docs/
COPY --chown=agent:agent fixtures/ fixtures/
COPY --chown=agent:agent scripts/ scripts/
COPY hidden-fixtures/ /opt/verifier-fixtures/

RUN chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output /app/state/srtctl /app/target \
    && chown -R agent:agent /app \
    && chmod -R a-w /app/docs /app/fixtures \
    && chmod -R 700 /opt/verifier-fixtures \
    && chown -R root:root /opt/verifier-fixtures /opt/verifier-venv /logs/verifier \
    && runuser -u agent -- cargo build --offline --release --locked -p srtctl \
    && install -o root -g root -m 0755 /app/target/release/srtctl /usr/local/bin/srtctl \
    && runuser -u agent -- /app/scripts/reset-state.sh
# No final USER directive: Harbor runs the agent as user=agent and the verifier as root.
# /tests, /opt/verifier-venv, /opt/verifier-fixtures, system tools, and /logs/verifier stay root-owned.
