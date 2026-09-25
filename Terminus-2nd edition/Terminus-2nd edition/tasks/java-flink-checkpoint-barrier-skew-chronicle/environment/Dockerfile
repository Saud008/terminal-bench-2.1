FROM public.ecr.aws/docker/library/maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e AS builder

WORKDIR /build
COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests package

FROM public.ecr.aws/docker/library/maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        patch \
        tmux \
        asciinema \
        python3 \
        python3-venv \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \
    && /opt/verifier-venv/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

ENV PATH="/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

WORKDIR /app
COPY pom.xml .
COPY src ./src
COPY docs ./docs
COPY fixtures ./fixtures
COPY scripts ./scripts
COPY hidden /opt/verifier-fixtures/flink_skew_hidden

COPY --from=builder /build/target/flink-skew.jar /app/bin/flink-skew.jar

RUN sed -i 's/\r$//' /app/scripts/*.sh \
    && find /app/src -name '*.java' -exec sed -i 's/\r$//' {} + \
    && chmod +x /app/scripts/rebuild-flink-skew.sh /app/scripts/reset-state.sh \
    && python3 /app/fixtures/build_fixtures.py \
    && mkdir -p /app/state /app/output /app/bin
