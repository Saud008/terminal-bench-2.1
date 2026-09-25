FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rustbuild

WORKDIR /app
ENV CARGO_INCREMENTAL=0

COPY Cargo.toml Cargo.lock rust-toolchain.toml ./

RUN mkdir -p src \
    && echo "pub fn placeholder() {}" > src/lib.rs \
    && echo "fn main() {}" > src/main.rs \
    && cargo fetch --locked

COPY src/ /app/src/

RUN cargo build --locked --release -p fbpkg

FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV CARGO_INCREMENTAL=0
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        flatbuffers-compiler \
        tmux \
        asciinema \
        python3=3.11.2-1+b1 \
        python3-pip \
        python3-venv \
        ca-certificates \
        bash \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/verifier-schema \
    && python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

COPY --from=rustbuild /usr/local/cargo /usr/local/cargo
COPY --from=rustbuild /usr/local/rustup /usr/local/rustup

WORKDIR /app
COPY Cargo.toml Cargo.lock rust-toolchain.toml README.md /app/
COPY src/ /app/src/
COPY docs/ /app/docs/
COPY schema/ /app/schema/
COPY schema/scene.fbs /opt/verifier-schema/scene.fbs
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY verifier-support/broken_lib /opt/verifier-broken-fbdecode/
COPY --from=rustbuild /app/target /app/target
COPY --from=rustbuild /app/target/release/fbdecode /usr/local/bin/fbdecode

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && chmod +x /app/scripts/reset-state.sh /app/scripts/verifier-rebuild.sh \
    && mkdir -p /app/output /app/state /logs/verifier
