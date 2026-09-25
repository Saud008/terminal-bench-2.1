FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
  tmux \
  asciinema \
  python3 \
  python3-venv \
  jq \
  coreutils \
  && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv
RUN /opt/verifier-venv/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

COPY tools/ /app/tools/
COPY lib/ /app/lib/
COPY scripts/ /app/scripts/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/

RUN mkdir -p /app/bin /app/state /app/output \
  && ln -sf /app/tools/udev-policy-planner /app/bin/udev-policy-planner \
  && chmod +x /app/tools/udev-policy-planner /app/scripts/rebuild-udevplan.sh \
  && find /app/lib -name '*.sh' -exec chmod +x {} \;

ENV PATH=/app/bin:/app/scripts:${PATH}
CMD ["bash", "-lc", "echo Environment ready"]
