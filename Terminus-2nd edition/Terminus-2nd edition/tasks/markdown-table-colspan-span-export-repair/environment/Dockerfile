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

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0
ENV CARGO_BUILD_JOBS=2
ENV RUSTFLAGS="-C debuginfo=0"

WORKDIR /app
COPY Cargo.toml Cargo.lock README.md /app/
COPY crates/ /app/crates/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY --chmod=0755 scripts/ /app/scripts/

RUN cargo vendor \
    && mkdir -p .cargo \
    && printf '[source.crates-io]\nreplace-with = "vendored-sources"\n\n[source.vendored-sources]\ndirectory = "vendor"\n' > .cargo/config.toml

ENV CARGO_NET_OFFLINE=true

RUN find /app/fixtures -type f \( -name '*.md' -o -name '*.json' \) -exec sed -i 's/\r$//' {} + \
    && sed -i 's/\r$//' /app/scripts/*.sh \
    && python3 /app/scripts/gen_manifest.py \
    && cargo build --offline --release --locked -p mdtable \
    && install -m 0755 /app/target/release/mdtable /usr/local/bin/mdtable \
    && mkdir -p /opt/fixture-seed/tables /app/output /app/state \
    && cp -a /app/fixtures/tables/. /opt/fixture-seed/tables/ \
    && install -m 0444 /app/fixtures/manifest.json /opt/fixture-seed/manifest.json \
    && find /opt/fixture-seed/tables -type f -exec install -m 0444 {} {} \; \
    && bash /app/scripts/reset-state.sh
