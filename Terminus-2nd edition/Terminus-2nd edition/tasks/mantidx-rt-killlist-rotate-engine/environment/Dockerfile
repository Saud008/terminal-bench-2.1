FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential=12.9 \
        pkg-config=1.8.1-1 \
        tmux=3.3a-3 \
        asciinema=2.2.0-1 \
        python3=3.11.2-1+b1 \
        python3-venv=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        ca-certificates=20230311+deb12u1 \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv
COPY requirements.lock /tmp/requirements.lock
RUN /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
    && rm -f /tmp/requirements.lock

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY crates/ crates/
COPY docs/ docs/
COPY fixtures/ fixtures/
COPY scripts/ scripts/
COPY README.md README.md

RUN cargo vendor \
    && mkdir -p .cargo \
    && printf '[source.crates-io]\nreplace-with = "vendored-sources"\n\n[source.vendored-sources]\ndirectory = "vendor"\n' > .cargo/config.toml

ENV CARGO_NET_OFFLINE=true

RUN cargo build --offline --locked --release --bin mantidx \
    && install -m 0755 target/release/mantidx /usr/local/bin/mantidx \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/*.sh \
    && mkdir -p /app/output /app/state /app/data \
    && bash /app/scripts/reset-state.sh
