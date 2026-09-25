FROM --platform=linux/amd64 public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        tmux \
        asciinema \
        python3 \
        python3-pip \
        python3-venv \
        coreutils \
        gawk \
        make \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==9.0.3 \
        pytest-json-ctrf==0.5.0

WORKDIR /app
COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY scripts/ /app/scripts/
COPY config/ /app/config/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY Makefile /app/Makefile
COPY fixtures-tb3/rig-delta/ /opt/verifier-fixtures/rig-delta/

RUN find /app/lib -name '*.sh' -exec sed -i 's/\r$//' {} + \
    && sed -i 's/\r$//' /app/scripts/*.sh /app/bin/rigbundle \
    && chmod +x /app/bin/rigbundle /app/scripts/*.sh \
    && make install \
    && mkdir -p /app/state /app/output

ENV PATH="/app/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
