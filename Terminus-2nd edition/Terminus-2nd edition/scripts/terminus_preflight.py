#!/usr/bin/env python3
"""Single preflight entry: CI + category + files (agents/hooks — no harbor GPT LLMaJ).

Usage:
  python3 scripts/terminus_preflight.py --task-dir tasks/<name>
  python3 scripts/terminus_preflight.py --task-dir tasks/<name> --pack-gate

Reports:
  jobs-local/ci-check-last.txt
  jobs-local/llmaj-check-last.txt (local quality heuristics only)
"""
from __future__ import annotations

import sys

from terminus_ci_check import main

if __name__ == "__main__":
    sys.exit(main())
