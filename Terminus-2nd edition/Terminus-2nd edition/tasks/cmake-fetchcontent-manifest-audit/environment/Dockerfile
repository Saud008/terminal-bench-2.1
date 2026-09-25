FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        coreutils \
        findutils \
        tar \
        cmake \
        ninja-build \
        build-essential \
        tmux \
        asciinema \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

WORKDIR /app

COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY docs/ /app/docs/
COPY project/ /app/project/
COPY vendor-cache/ /app/vendor-cache/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md

RUN find /app/lib /app/scripts /app/bin -type f -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/bin/cmake-audit /app/scripts/*.sh \
    && find /app/lib -name '*.sh' -exec chmod +x {} \; \
    && mkdir -p /app/data /app/output /app/state /app/build /app/install \
    && cmake -S /app/project -B /app/build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/app/install \
    && cmake --build /app/build \
    && cmake --install /app/build \
    && ln -sfn libfoo.a /app/install/lib/libfoo.so \
    && bash /app/scripts/reset-state.sh

ENV PATH="/app/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
