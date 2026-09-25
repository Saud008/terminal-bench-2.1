FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv
COPY requirements.lock /tmp/requirements.lock
RUN /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY src/ src/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY config/ config/
COPY scripts/ scripts/
COPY opt-verifier-fixtures/ /opt/verifier-fixtures/
COPY README.md README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output /app/state /app/data \
    && cargo build --locked --release --bin blevectl \
    && install -m 0755 target/release/blevectl /usr/local/bin/blevectl \
    && bash /app/scripts/reset-state.sh
