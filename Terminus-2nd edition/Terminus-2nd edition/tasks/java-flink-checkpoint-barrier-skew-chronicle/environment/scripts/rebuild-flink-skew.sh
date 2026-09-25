#!/usr/bin/env bash
set -euo pipefail
cd /app
python3 /app/fixtures/build_fixtures.py
mvn -q -DskipTests package
cp /app/target/flink-skew.jar /app/bin/flink-skew.jar
