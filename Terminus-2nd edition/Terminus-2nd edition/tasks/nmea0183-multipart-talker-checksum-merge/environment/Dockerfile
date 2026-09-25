FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY crates/ /app/crates/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md
COPY verifier-fixtures/ /opt/verifier-fixtures/

RUN find /app/scripts -name '*.sh' -exec sed -i 's/\r$//' {} + \
 && chmod +x /app/scripts/reset-state.sh \
 && cargo build --release --locked -p nmeapipeline \
 && install -m 0755 /app/target/release/nmeapipeline /usr/local/bin/nmeapipeline \
 && mkdir -p /app/output /app/state \
 && bash /app/scripts/reset-state.sh
