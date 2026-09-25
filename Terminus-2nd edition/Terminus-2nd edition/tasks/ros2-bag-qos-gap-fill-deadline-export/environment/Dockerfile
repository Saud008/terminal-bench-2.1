FROM --platform=linux/amd64 public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes --no-deps -r /tmp/requirements.lock \
 && rm -f /tmp/requirements.lock

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0
ENV CARGO_BUILD_JOBS=2

RUN ln -sf /usr/local/cargo/bin/cargo /usr/local/bin/cargo \
 && ln -sf /usr/local/cargo/bin/rustc /usr/local/bin/rustc \
 && ln -sf /usr/local/cargo/bin/rustdoc /usr/local/bin/rustdoc \
 && printf '%s\n' 'export PATH="/usr/local/cargo/bin:${PATH}"' > /etc/profile.d/cargo-env.sh \
 && chmod 644 /etc/profile.d/cargo-env.sh \
 && printf '%s\n' 'export PATH="/usr/local/cargo/bin:${PATH}"' >> /root/.bashrc

COPY Cargo.toml Cargo.lock ./
COPY crates/ /app/crates/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md

RUN sed -i 's/\r$//' /app/scripts/*.sh \
 && chmod +x /app/scripts/*.sh \
 && mkdir -p /app/output \
 && cargo build --release --locked -p bag-audit \
 && install -m 0755 /app/target/release/bag-audit /usr/local/bin/bag-audit \
 && mkdir -p /opt/verifier-broken-bag \
 && cp /app/crates/bag-audit/src/bag/read.rs /opt/verifier-broken-bag/read.rs \
 && cp /app/crates/bag-audit/src/bag/gap.rs /opt/verifier-broken-bag/gap.rs \
 && cp /app/crates/bag-audit/src/qos/deadline.rs /opt/verifier-broken-bag/deadline.rs \
 && cp /app/crates/bag-audit/src/export/sqlite.rs /opt/verifier-broken-bag/sqlite.rs
