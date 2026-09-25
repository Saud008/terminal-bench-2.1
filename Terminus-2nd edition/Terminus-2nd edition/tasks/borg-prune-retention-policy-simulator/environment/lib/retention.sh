#!/usr/bin/env bash
# Retention bucket evaluation engine.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/clock_skew.sh"
source "${APP_ROOT}/lib/holds.sh"

evaluate_retention_json() {
  local stage_file="$1"
  local policy_file="$2"
  local holds_file="$3"
  local reference_now="$4"
  python3 - "${stage_file}" "${policy_file}" "${holds_file}" "${reference_now}" <<'PY'
import json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

stage_path, policy_path, holds_path, ref_s = sys.argv[1:5]
stage = json.loads(Path(stage_path).read_text(encoding="utf-8"))
policy = json.loads(Path(policy_path).read_text(encoding="utf-8"))
holds = json.loads(Path(holds_path).read_text(encoding="utf-8"))
ref = datetime.fromisoformat(ref_s.replace("Z", "+00:00")).astimezone(timezone.utc)
skew = int(policy.get("clock_skew_sec", 0))
week_start = policy.get("week_start", "monday")

def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)

def week_start_date(d, ws):
    if ws == "monday":
        return d - timedelta(days=d.weekday())
    return d - timedelta(days=(d.weekday() + 1) % 7)

archives = stage["archives"]
normalized = {}
clock_skew_adjusted = []
for a in archives:
    ts = parse_ts(a["ts"])
    normalized[a["name"]] = ts

def held(name):
    if name in holds.get("exact", []):
        return True
    for p in holds.get("prefix", []):
        if p in name:
            return True
    return False

kept = set()
legal = []
for a in archives:
    if held(a["name"]):
        kept.add(a["name"])
        legal.append(a["name"])

bucket_hits = {"daily": [], "weekly": [], "monthly": [], "yearly": []}

def pick(cands):
    if not cands:
        return None
    return max(cands, key=lambda a: (normalized[a["name"]], a["line"]))

# daily
ref_date = ref.date()
for i in range(int(policy["keep_daily"])):
    day = ref_date - timedelta(days=i)
    cands = [a for a in archives if normalized[a["name"]].date() == day]
    best = pick(cands)
    if best:
        kept.add(best["name"])
        bucket_hits["daily"].append(best["name"])

# weekly
for i in range(int(policy["keep_weekly"])):
    probe = ref_date - timedelta(days=7 * i)
    wk = week_start_date(probe, "sunday")
    cands = [a for a in archives if week_start_date(normalized[a["name"]].date(), "sunday") == wk]
    best = pick(cands)
    if best:
        kept.add(best["name"])
        bucket_hits["weekly"].append(best["name"])

# monthly
y, m = ref_date.year, ref_date.month
for _ in range(int(policy["keep_monthly"])):
    cands = [a for a in archives if (normalized[a["name"]].year, normalized[a["name"]].month) == (y, m)]
    best = pick(cands)
    if best:
        kept.add(best["name"])
        bucket_hits["monthly"].append(best["name"])
    m -= 1
    if m == 0:
        m = 12
        y -= 1

# yearly
y = ref_date.year
for _ in range(int(policy["keep_yearly"])):
    cands = [a for a in archives if normalized[a["name"]].year == y]
    best = pick(cands)
    if best:
        kept.add(best["name"])
        bucket_hits["yearly"].append(best["name"])
    y -= 1

all_names = {a["name"] for a in archives}
pruned = sorted(all_names - kept)
kept_sorted = sorted(kept)
evaluation = {
    "bucket_hits": bucket_hits,
    "clock_skew_adjusted": sorted(clock_skew_adjusted),
    "kept": kept_sorted,
    "legal_hold_kept": sorted(set(legal)),
    "pruned": pruned,
}
print(json.dumps(evaluation, sort_keys=True, separators=(",", ":")))
PY
}
