FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        make \
        python3 \
        python3-pip \
        python3-venv \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

WORKDIR /app
COPY lib/ /app/lib/
COPY src/ /app/src/
COPY tools/ /app/tools/
COPY docs/ /app/docs/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md

RUN find /app/scripts /app/lib /app/tools -type f \( -name '*.sh' -o -name 'demo-index' -o -name 'gendemo.py' \) -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/demo-index /app/scripts/*.sh \
    && mkdir -p /app/bin /app/output \
    && install -m 0755 /app/scripts/demo-index /app/bin/demo-index \
    && bash /app/scripts/build.sh \
    && bash /app/scripts/build-fixtures.sh \
    && mkdir -p /opt/verifier-fixtures/demos \
    && cp -a /app/fixtures/demos/beta/early.dem /opt/verifier-fixtures/demos/hidden-twist.dem \
    && cp -a /app/fixtures/demos/alpha/late.dem /opt/verifier-fixtures/demos/hidden-merge.dem \
    && mkdir -p /opt/fixture-seed/demos \
    && cp -a /app/fixtures/demos/. /opt/fixture-seed/demos/
