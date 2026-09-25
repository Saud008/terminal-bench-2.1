FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
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
COPY docker/build_hidden_fixtures.py /app/docker/build_hidden_fixtures.py

RUN mkdir -p /opt/verifier-broken-mavcore /opt/verifier-fixtures/mavlink \
 && find /app/scripts -name '*.sh' -exec sed -i 's/\r$//' {} + \
 && chmod +x /app/scripts/reset-state.sh \
 && cargo build --release --locked --bin mavctl \
 && install -m 0755 /app/target/release/mavctl /usr/local/bin/mavctl \
 && python3 /app/docker/build_hidden_fixtures.py \
 && mkdir -p /app/output /app/state \
 && bash /app/scripts/reset-state.sh

COPY verifier-broken/parse.rs /opt/verifier-broken-mavcore/parse.rs
COPY verifier-broken/validate.rs /opt/verifier-broken-mavcore/validate.rs
COPY verifier-broken/seed.rs /opt/verifier-broken-mavcore/seed.rs
COPY verifier-broken/session.rs /opt/verifier-broken-mavcore/session.rs
COPY verifier-broken/dedup.rs /opt/verifier-broken-mavcore/dedup.rs
COPY verifier-broken/checkpoint.rs /opt/verifier-broken-mavcore/checkpoint.rs
COPY verifier-broken/fact_diff.rs /opt/verifier-broken-mavcore/fact_diff.rs
COPY verifier-broken/route.rs /opt/verifier-broken-mavcore/route.rs
COPY verifier-broken/publish.rs /opt/verifier-broken-mavcore/publish.rs
COPY verifier-broken/decode.rs /opt/verifier-broken-mavcore/decode.rs
