#!/usr/bin/env python3
"""Ensure output/state dirs exist at image build."""

from pathlib import Path

Path("/app/output").mkdir(parents=True, exist_ok=True)
print("ok")
