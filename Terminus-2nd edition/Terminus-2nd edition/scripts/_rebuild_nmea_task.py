#!/usr/bin/env python3
"""Rebuild nmea0183-multipart-talker-checksum-merge task tree."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "nmea0183-multipart-talker-checksum-merge"
ENV = TASK / "environment"
SRC = ENV / "crates" / "nmeapipeline" / "src"
SOL = TASK / "solution"
TESTS = TASK / "tests"


def w(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n") if content.startswith("\n") else content, encoding="utf-8")
    if not content.endswith("\n"):
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")


def main() -> None:
    # --- task.toml ---
    w(
        TASK / "task.toml",
        '''version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous@gmail.com"
difficulty = "hard"
category = "software-engineering"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["rust"]
tags = ["nmea0183", "multipart", "talker", "checksum", "merge"]
expert_time_estimate_min = 240
junior_time_estimate_min = 480

[agent]
timeout_sec = 1800

[verifier]
timeout_sec = 900

[environment]
allow_internet = false
build_timeout_sec = 900.0
cpus = 2
memory_mb = 4096
storage_mb = 10240
workdir = "/app"
''',
    )

    w(
        ENV / ".dockerignore",
        """.git
.gitignore
target/
**/__pycache__/
__pycache__/
*.pyc
**/*.pyc
.pytest_cache
**/.pytest_cache/
.mypy_cache
**/.mypy_cache/
.ruff_cache
**/.ruff_cache/
node_modules/
**/node_modules/
output/
solution/
tests/
""",
    )

    w(
        ENV / "Dockerfile",
        """FROM public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36

RUN apt-get update \\
 && apt-get install -y --no-install-recommends \\
    asciinema \\
    ca-certificates \\
    python3 \\
    python3-pip \\
    python3-venv \\
    tmux \\
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/verifier-venv \\
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \\
 && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
ENV CARGO_INCREMENTAL=0

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY crates/ /app/crates/
COPY docs/ /app/docs/
COPY fixtures/ /app/fixtures/
COPY scripts/ /app/scripts/
COPY README.md /app/README.md
COPY verifier-fixtures/ /opt/verifier-fixtures/

RUN find /app/scripts -name '*.sh' -exec sed -i 's/\\r$//' {} + \\
 && chmod +x /app/scripts/reset-state.sh \\
 && cargo build --release --locked -p nmeapipeline \\
 && install -m 0755 /app/target/release/nmeapipeline /usr/local/bin/nmeapipeline \\
 && mkdir -p /app/output /app/state \\
 && bash /app/scripts/reset-state.sh
""",
    )

    w(
        ENV / "Cargo.toml",
        """[workspace]
resolver = "2"
members = ["crates/nmeapipeline"]

[workspace.package]
edition = "2021"
version = "0.1.0"

[workspace.dependencies]
clap = { version = "4.6.1", features = ["derive"] }
serde = { version = "1.0.228", features = ["derive"] }
serde_json = "1.0.150"
sha2 = "0.10.9"
hex = "0.4.3"
""",
    )

    w(
        ENV / "crates" / "nmeapipeline" / "Cargo.toml",
        """[package]
name = "nmeapipeline"
version.workspace = true
edition.workspace = true

[[bin]]
name = "nmeapipeline"
path = "src/main.rs"

[dependencies]
clap = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
sha2 = { workspace = true }
hex = { workspace = true }
""",
    )

    w(
        ENV / "README.md",
        """# nmeapipeline

Offline NMEA0183 multipart merge utility.

```
nmeapipeline merge --input PATH --output /app/output/merge-report.json [--state /app/state/merge-session.json]
```

Contracts: `/app/docs/merge-contract.md`, `/app/docs/report-schema.md`, `/app/docs/merge-snapshot.md`.
""",
    )

    w(
        ENV / "scripts" / "reset-state.sh",
        """#!/usr/bin/env bash
set -euo pipefail
rm -f /app/output/*.json 2>/dev/null || true
rm -f /app/state/*.json 2>/dev/null || true
mkdir -p /app/output /app/state
""",
    )

    # Docs
    w(
        ENV / "docs" / "merge-contract.md",
        """# Merge contract

## Checksum
XOR every byte after the leading `$` up to (but not including) `*`. Compare to the two hex digits after `*`. Invalid checksum lines are rejected.

## Quoted fields
Split on commas outside quotes. Surrounding double quotes are **preserved** in field values. Inside quotes, `""` becomes a single `"`.

## Talker normalization
Canonical talker for merge keys: `GP` and `GN` both become `GN`. Other talkers (including `GL`) stay unchanged. Merge key format: `{canonical_talker}:{sentence}:{multipart_total}`.

## Multipart
Multipart sentences have `fields[0]` = total fragments and `fields[1]` = message number (1-based). Payload concatenates fields from index **3** onward, sorted by message number ascending.

## Single-pass vs session
Without `--state`, incomplete multipart groups (missing fragments) are still emitted in the report.
With `--state PATH`, incomplete groups are buffered in session pending and **not** reported. Orphan fragments that do not include message number `1` are dropped (not persisted). When a new valid RMC date differs from the stored session date, all pending buckets are discarded.

## Duplicate fragments
When pending fragments merge with new input for the same merge key, duplicate message numbers keep the fragment that arrived **later** in the combined pending-plus-input sequence.

## RMC date context
Only RMC sentences with navigation status field `A` update `rmc_date` / `rmc_time`. Status `V` (or other) must not update context. Time-only sentences attach UTC using the latest valid RMC date; midnight rollover advances the calendar across month and year boundaries (including leap days).

## Export
Export reads `/app/state/merge-snapshot.json`, verifies digest, validates talker prefixes, and builds the report from snapshot fields only — never by re-parsing the input stream.
""",
    )

    w(
        ENV / "docs" / "report-schema.md",
        """# Report schema (`/app/output/merge-report.json`)

```json
{
  "groups": [
    {
      "merge_key": "GN:GSV:2",
      "talker": "GN",
      "sentence": "GSV",
      "multipart_total": 2,
      "fragments_merged": 2,
      "payload_fields": ["..."],
      "utc_iso": "2024-01-01T00:00:01Z"
    }
  ],
  "rejected": [{"line": "...", "reason": "checksum"}],
  "snapshot_digest": "<sha256 hex>"
}
```

Groups appear in first-seen stream order of their merge keys. `utc_iso` may be `null` when no RMC context applies.
""",
    )

    w(
        ENV / "docs" / "merge-snapshot.md",
        """# Merge snapshot (`/app/state/merge-snapshot.json`)

```json
{
  "groups": [ /* same shape as report groups */ ],
  "rejected": [ /* same as report */ ],
  "snapshot_digest": "<sha256 hex>"
}
```

`snapshot_digest` is SHA-256 hex of the UTF-8 bytes of compact JSON `{"groups":[...],"rejected":[...]}` where `groups` and `rejected` are sorted by `merge_key` / `line` respectively (stable lexicographic), with separators `,` and `:` and no whitespace.

## Export gate

`export::staging::publish_export` reads the snapshot, verifies `snapshot_digest` via `export::writer::verify_digest`, runs `export::validate::validate_snapshot`, and writes the merge report through `export::wrap::build_report` using snapshot fields only.

`export::validate::validate_snapshot` requires each group's `merge_key` to begin with `{talker}:`. Incomplete multipart groups (`fragments_merged < multipart_total`) are allowed in single-pass snapshots.
""",
    )

    # Fixtures
    def nmea_line(body: str) -> str:
        assert body.startswith("$")
        xor = 0
        for ch in body[1:]:
            xor ^= ord(ch)
        return f"{body}*{xor:02X}"

    baseline = "\n".join(
        [
            nmea_line("$GPRMC,235959.00,A,4807.038,N,01131.000,E,022.4,084.4,311223,,,A"),
            nmea_line("$GPGSV,2,2,08,01,05,111,00,13,06,292,00"),
            nmea_line('$GPGSV,2,1,08,11,40,083,46,02,17,308,"hi""x"'),
            nmea_line("$GNGSA,A,3,04,05,09,12,24,25,,,,,,,1.5,0.8,1.2"),
            nmea_line("$GNGSA,A,3,04,05,,,,,,,1.6,0.9,1.3"),  # will be multipart-ish via fields - actually GSA not typically multipart; use as single
        ]
    )
    # Make GSV properly multipart 2 fragments
    baseline = "\n".join(
        [
            nmea_line("$GPRMC,235959.00,A,4807.038,N,01131.000,E,022.4,084.4,311223,,,A"),
            nmea_line("$GPGSV,2,2,08,01,05,111,00,13,06,292,00"),
            nmea_line('$GPGSV,2,1,08,11,40,083,46,02,17,308,"hi""x"'),
            nmea_line("$GLGSV,2,1,04,65,62,157,44,66,45,240,42"),
            nmea_line("$GLGSV,2,2,04,67,12,090,30,68,08,180,25"),
            nmea_line("$GPGSA,A,3,04,05,09,12,,,,,1.5,0.8,1.2"),
        ]
    ) + "\n"
    w(ENV / "fixtures" / "streams" / "baseline.nmea", baseline)

    # Hidden verifier fixtures
    w(
        ENV / "verifier-fixtures" / "gsa-order.nmea",
        "\n".join(
            [
                nmea_line("$GPRMC,120000.00,A,4807.038,N,01131.000,E,022.4,084.4,010124,,,A"),
                nmea_line("$GPGSA,A,3,24,25,,,,,,,2.0,1.0,1.5"),
                nmea_line("$GPGSA,A,3,04,05,09,12,,,,,1.5,0.8,1.2"),
            ]
        )
        + "\n",
    )
    w(
        ENV / "verifier-fixtures" / "duplicate-replay-part2.nmea",
        (TESTS / "hidden_bundles" / "duplicate-replay-part2.nmea").read_text(encoding="utf-8")
        if (TESTS / "hidden_bundles" / "duplicate-replay-part2.nmea").exists()
        else "\n".join(
            [
                nmea_line("$GPGSV,2,1,08,22,50,090,50,05,20,310,44"),
                nmea_line("$GNGSV,2,2,08,33,06,122,42,04,12,311,43"),
            ]
        )
        + "\n",
    )

    # ---- Rust sources: model + modules ----
    write_rust_sources()
    write_solution()
    write_tests(nmea_line)
    print(f"Wrote task under {TASK}")


def write_rust_sources() -> None:
    w(
        SRC / "model.rs",
        """use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ParsedSentence {
    pub raw: String,
    pub talker: String,
    pub sentence: String,
    pub fields: Vec<String>,
    pub is_multipart: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MergeGroup {
    pub merge_key: String,
    pub talker: String,
    pub sentence: String,
    pub multipart_total: u32,
    pub fragments_merged: u32,
    pub payload_fields: Vec<String>,
    pub utc_iso: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RejectedLine {
    pub line: String,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MergeSnapshot {
    pub groups: Vec<MergeGroup>,
    pub rejected: Vec<RejectedLine>,
    pub snapshot_digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MergeReport {
    pub groups: Vec<MergeGroup>,
    pub rejected: Vec<RejectedLine>,
    pub snapshot_digest: String,
}
""",
    )

    # BROKEN checksum: XORs including '$'
    w(
        SRC / "checksum.rs",
        """/// BROKEN: includes the leading '$' in the XOR window.
pub fn verify_checksum(line: &str) -> bool {
    let Some(star) = line.rfind('*') else { return false; };
    if star + 3 > line.len() { return false; }
    let body = &line[..star];
    let claimed = &line[star + 1..star + 3];
    let mut v = 0u8;
    for b in body.bytes() {
        v ^= b;
    }
    format!("{v:02X}").eq_ignore_ascii_case(claimed)
}

pub fn compute_checksum_body(body_after_dollar: &str) -> String {
    let mut v = 0u8;
    for b in body_after_dollar.bytes() {
        v ^= b;
    }
    format!("{v:02X}")
}
""",
    )

    w(
        SRC / "parse" / "mod.rs",
        """pub mod fields;
""",
    )

    # BROKEN: strips surrounding quotes
    w(
        SRC / "parse" / "fields.rs",
        """use crate::checksum;
use crate::model::ParsedSentence;

/// BROKEN: strips surrounding quotes from fields.
pub fn parse_line(line: &str) -> Result<ParsedSentence, String> {
    let line = line.trim();
    if !line.starts_with('$') || !checksum::verify_checksum(line) {
        return Err("checksum".into());
    }
    let star = line.rfind('*').unwrap();
    let body = &line[1..star];
    let mut parts = split_fields(body);
    if parts.is_empty() {
        return Err("empty".into());
    }
    let addr = parts.remove(0);
    if addr.len() < 5 {
        return Err("addr".into());
    }
    let talker = addr[..2].to_string();
    let sentence = addr[2..].to_string();
    let is_multipart = matches!(sentence.as_str(), "GSV" | "GSA") && parts.len() >= 2
        && parts[0].parse::<u32>().ok().filter(|&t| t > 1).is_some();
    Ok(ParsedSentence {
        raw: line.to_string(),
        talker,
        sentence,
        fields: parts,
        is_multipart,
    })
}

fn split_fields(body: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    let mut in_quotes = false;
    let chars: Vec<char> = body.chars().collect();
    let mut i = 0;
    while i < chars.len() {
        let c = chars[i];
        if in_quotes {
            if c == '"' {
                if i + 1 < chars.len() && chars[i + 1] == '"' {
                    cur.push('"');
                    i += 2;
                    continue;
                }
                in_quotes = false;
                i += 1;
                continue;
            }
            cur.push(c);
            i += 1;
            continue;
        }
        if c == '"' {
            in_quotes = true;
            i += 1;
            continue;
        }
        if c == ',' {
            out.push(cur);
            cur = String::new();
            i += 1;
            continue;
        }
        cur.push(c);
        i += 1;
    }
    out.push(cur);
    out
}
""",
    )

    w(
        SRC / "talker" / "mod.rs",
        """pub mod normalize;
""",
    )

    # BROKEN: identity only
    w(
        SRC / "talker" / "normalize.rs",
        """/// BROKEN: does not canonicalize GP/GN to GN.
pub fn canonical_talker(talker: &str) -> String {
    talker.to_string()
}
""",
    )

    w(
        SRC / "merge" / "mod.rs",
        """pub mod accumulate;
pub mod compose;
pub mod datetime;
pub mod multipart;
""",
    )

    # BROKEN: payload from index 2
    w(
        SRC / "merge" / "multipart.rs",
        """use crate::model::ParsedSentence;

/// BROKEN: concatenates from field index 2 instead of 3.
pub fn merge_payload(fragments: &[ParsedSentence]) -> (u32, u32, Vec<String>) {
    let mut sorted = fragments.to_vec();
    sorted.sort_by_key(|s| s.fields.get(1).and_then(|v| v.parse::<u32>().ok()).unwrap_or(0));
    let total = sorted
        .first()
        .and_then(|s| s.fields.first())
        .and_then(|v| v.parse().ok())
        .unwrap_or(1);
    let mut payload = Vec::new();
    for s in &sorted {
        if s.fields.len() > 2 {
            payload.extend(s.fields[2..].iter().cloned());
        }
    }
    (total, sorted.len() as u32, payload)
}

pub fn merge_key(talker: &str, sentence: &str, total: u32) -> String {
    format!("{talker}:{sentence}:{total}")
}
""",
    )

    # Decoy accumulate
    w(
        SRC / "merge" / "accumulate.rs",
        """use crate::model::{MergeGroup, ParsedSentence};

/// Legacy decoy path — not on the hot path. Wrong merge order.
pub fn accumulate_groups(sentences: &[ParsedSentence]) -> Vec<MergeGroup> {
    sentences
        .iter()
        .map(|s| MergeGroup {
            merge_key: format!("{}:{}:1", s.talker, s.sentence),
            talker: s.talker.clone(),
            sentence: s.sentence.clone(),
            multipart_total: 1,
            fragments_merged: 1,
            payload_fields: s.fields.clone(),
            utc_iso: None,
        })
        .collect()
}
""",
    )

    # BROKEN datetime: no month/year rollover
    w(
        SRC / "merge" / "datetime.rs",
        """/// BROKEN: naive midnight bump without calendar rollover.
pub fn attach_utc(rmc_date: Option<&str>, rmc_time: Option<&str>, time_field: &str) -> Option<String> {
    let date = rmc_date?;
    if date.len() != 6 {
        return None;
    }
    let day: u32 = date[0..2].parse().ok()?;
    let month: u32 = date[2..4].parse().ok()?;
    let year: u32 = 2000 + date[4..6].parse::<u32>().ok()?;
    let (hh, mm, ss) = parse_time(time_field)?;
    // If time suggests after midnight relative to stored RMC time, bump day only (broken)
    let mut d = day;
    let mut m = month;
    let mut y = year;
    if let Some(rt) = rmc_time {
        if let Some((rh, _, _)) = parse_time(rt) {
            if hh < rh {
                d += 1;
                // BROKEN: no month/year clamp
            }
        }
    }
    Some(format!("{y:04}-{m:02}-{d:02}T{hh:02}:{mm:02}:{ss:02}Z"))
}

fn parse_time(t: &str) -> Option<(u32, u32, u32)> {
    if t.len() < 6 {
        return None;
    }
    let hh = t[0..2].parse().ok()?;
    let mm = t[2..4].parse().ok()?;
    let ss = t[4..6].parse().ok()?;
    Some((hh, mm, ss))
}

pub fn days_in_month(year: u32, month: u32) -> u32 {
    match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            if year % 4 == 0 && (year % 100 != 0 || year % 400 == 0) {
                29
            } else {
                28
            }
        }
        _ => 30,
    }
}
""",
    )

    # BROKEN compose: uses accumulate decoy path partially / wrong talker
    w(
        SRC / "merge" / "compose.rs",
        """use std::collections::HashMap;

use crate::merge::{datetime, multipart};
use crate::model::{MergeGroup, ParsedSentence, RejectedLine};
use crate::session::pending::PendingStore;
use crate::talker::normalize;

pub struct ComposeResult {
    pub groups: Vec<MergeGroup>,
    pub rejected: Vec<RejectedLine>,
    pub rmc_date: Option<String>,
    pub rmc_time: Option<String>,
    pub pending: PendingStore,
}

/// BROKEN: does not sort fragments, uses raw talker in keys, emits session incompletes.
pub fn compose_stream(
    sentences: Vec<ParsedSentence>,
    mut pending: PendingStore,
    mut rmc_date: Option<String>,
    mut rmc_time: Option<String>,
    use_session: bool,
) -> ComposeResult {
    let mut rejected = Vec::new();
    let mut buckets: HashMap<String, Vec<ParsedSentence>> = HashMap::new();
    let mut order: Vec<String> = Vec::new();
    let mut singles: Vec<MergeGroup> = Vec::new();

    for s in sentences {
        if s.sentence == "RMC" {
            // context update handled outside; still emit as single
        }
        if s.is_multipart {
            let talker = s.talker.clone(); // BROKEN: no canonical
            let total = s.fields.first().and_then(|v| v.parse().ok()).unwrap_or(1);
            let key = multipart::merge_key(&talker, &s.sentence, total);
            if !buckets.contains_key(&key) {
                order.push(key.clone());
                let prior = pending.take_fragments(&key);
                buckets.insert(key.clone(), prior);
            }
            buckets.get_mut(&key).unwrap().push(s);
        } else {
            let talker = normalize::canonical_talker(&s.talker);
            let key = format!("{talker}:{}:1", s.sentence);
            let utc = s.fields.first().and_then(|t| {
                datetime::attach_utc(rmc_date.as_deref(), rmc_time.as_deref(), t)
            });
            if !order.contains(&key) {
                order.push(key.clone());
            }
            singles.push(MergeGroup {
                merge_key: key,
                talker,
                sentence: s.sentence.clone(),
                multipart_total: 1,
                fragments_merged: 1,
                payload_fields: s.fields.clone(),
                utc_iso: utc,
            });
        }
    }

    let mut groups = Vec::new();
    let mut seen_single = std::collections::HashSet::new();
    for key in &order {
        if let Some(frags) = buckets.remove(key) {
            let combined = if use_session {
                pending.merge_with_pending(key, frags)
            } else {
                frags
            };
            pending.finalize_bucket(key.clone(), combined, use_session, &mut groups);
        } else if let Some(g) = singles.iter().find(|g| &g.merge_key == key) {
            if seen_single.insert(g.merge_key.clone()) {
                groups.push(g.clone());
            }
        }
    }
    for g in singles {
        if seen_single.insert(g.merge_key.clone()) {
            groups.push(g);
        }
    }

    let _ = (&mut rmc_date, &mut rmc_time, &mut rejected);
    ComposeResult {
        groups,
        rejected,
        rmc_date,
        rmc_time,
        pending,
    }
}
""",
    )

    w(
        SRC / "context" / "mod.rs",
        """pub mod rmc;
""",
    )

    # BROKEN: accepts V status
    w(
        SRC / "context" / "rmc.rs",
        """use crate::model::ParsedSentence;

/// BROKEN: updates date context even when status is not A.
pub fn update_rmc_context(
    sentence: &ParsedSentence,
    rmc_date: &mut Option<String>,
    rmc_time: &mut Option<String>,
) -> bool {
    if sentence.sentence != "RMC" || sentence.fields.len() < 9 {
        return false;
    }
    let status = sentence.fields.get(1).map(|s| s.as_str()).unwrap_or("");
    let _ = status; // BROKEN: ignore status
    let time = sentence.fields[0].clone();
    let date = sentence.fields[8].clone();
    if date.len() == 6 && time.len() >= 6 {
        *rmc_time = Some(time);
        *rmc_date = Some(date);
        return true;
    }
    false
}
""",
    )

    w(
        SRC / "session" / "mod.rs",
        """pub mod pending;
pub mod reconcile;
pub mod store;
""",
    )

    w(
        SRC / "session" / "store.rs",
        """use serde::{Deserialize, Serialize};

use crate::model::ParsedSentence;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PendingGroup {
    pub merge_key: String,
    pub talker: String,
    pub sentence: String,
    pub multipart_total: u32,
    pub fragments: Vec<ParsedSentence>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SessionState {
    pub version: u32,
    pub rmc_date: Option<String>,
    pub rmc_time: Option<String>,
    pub pending: Vec<PendingGroup>,
}

impl Default for SessionState {
    fn default() -> Self {
        Self {
            version: 1,
            rmc_date: None,
            rmc_time: None,
            pending: Vec::new(),
        }
    }
}
""",
    )

    # Broken reconcile: keep earliest
    w(
        SRC / "session" / "reconcile.rs",
        """use std::collections::HashMap;

use crate::model::ParsedSentence;

/// BROKEN: keeps earliest fragment for duplicate message numbers.
pub fn reconcile_fragments(fragments: Vec<ParsedSentence>) -> Vec<ParsedSentence> {
    let mut by_num: HashMap<String, ParsedSentence> = HashMap::new();
    for sentence in fragments {
        let num = sentence
            .fields
            .get(1)
            .cloned()
            .unwrap_or_else(|| "0".to_string());
        by_num.entry(num).or_insert(sentence);
    }
    let mut out: Vec<ParsedSentence> = by_num.into_values().collect();
    out.sort_by_key(|sentence| {
        sentence
            .fields
            .get(1)
            .and_then(|v| v.parse::<u32>().ok())
            .unwrap_or(0)
    });
    out
}
""",
    )

    # Broken pending (emit incomplete in session) — use surviving broken version semantics
    w(
        SRC / "session" / "pending.rs",
        """use std::collections::HashMap;

use crate::merge::multipart;
use crate::model::{MergeGroup, ParsedSentence};
use crate::session::store::PendingGroup;

pub struct PendingStore {
    groups: HashMap<String, Vec<ParsedSentence>>,
}

impl PendingStore {
    pub fn new() -> Self {
        Self { groups: HashMap::new() }
    }

    pub fn from_groups(groups: Vec<PendingGroup>) -> Self {
        let mut map = HashMap::new();
        for group in groups {
            map.insert(group.merge_key, group.fragments);
        }
        Self { groups: map }
    }

    pub fn into_groups(self) -> Vec<PendingGroup> {
        self.groups
            .into_iter()
            .map(|(merge_key, fragments)| {
                let first = fragments.first().cloned().unwrap_or(ParsedSentence {
                    raw: String::new(),
                    talker: String::new(),
                    sentence: String::new(),
                    fields: Vec::new(),
                    is_multipart: true,
                });
                let talker = crate::talker::normalize::canonical_talker(&first.talker);
                let sentence = first.sentence.clone();
                let multipart_total = first
                    .fields
                    .first()
                    .and_then(|v| v.parse().ok())
                    .unwrap_or(1);
                PendingGroup {
                    merge_key,
                    talker,
                    sentence,
                    multipart_total,
                    fragments,
                }
            })
            .collect()
    }

    pub fn clear_all(&mut self) {
        self.groups.clear();
    }

    pub fn is_empty(&self) -> bool {
        self.groups.is_empty()
    }

    pub fn take_fragments(&mut self, merge_key: &str) -> Vec<ParsedSentence> {
        self.groups.remove(merge_key).unwrap_or_default()
    }

    pub fn stash_incomplete(&mut self, merge_key: String, fragments: Vec<ParsedSentence>) {
        self.groups.insert(merge_key, fragments);
    }

    pub fn group_from_bucket(
        &self,
        merge_key: &str,
        fragments: &[ParsedSentence],
        emit_incomplete: bool,
    ) -> Option<MergeGroup> {
        if fragments.is_empty() {
            return None;
        }
        let first = &fragments[0];
        let talker = crate::talker::normalize::canonical_talker(&first.talker);
        let (multipart_total, fragments_merged, payload_fields) =
            multipart::merge_payload(fragments);
        if !emit_incomplete && fragments_merged < multipart_total {
            return None;
        }
        Some(MergeGroup {
            merge_key: merge_key.to_string(),
            talker,
            sentence: first.sentence.clone(),
            multipart_total,
            fragments_merged,
            payload_fields,
            utc_iso: None,
        })
    }

    pub fn finalize_bucket(
        &mut self,
        merge_key: String,
        fragments: Vec<ParsedSentence>,
        use_session: bool,
        out: &mut Vec<MergeGroup>,
    ) {
        if fragments.is_empty() {
            return;
        }
        let has_one = fragments.iter().any(|f| f.fields.get(1).map(|v| v == "1").unwrap_or(false));
        // BROKEN: keeps orphans without fragment one
        let total = fragments[0]
            .fields
            .first()
            .and_then(|v| v.parse::<u32>().ok())
            .unwrap_or(1);
        let merged = fragments.len() as u32;
        if use_session && merged < total {
            self.stash_incomplete(merge_key.clone(), fragments.clone());
            if let Some(group) = self.group_from_bucket(&merge_key, &fragments, true) {
                out.push(group);
            }
            let _ = has_one;
            return;
        }
        if let Some(group) = self.group_from_bucket(&merge_key, &fragments, true) {
            out.push(group);
        }
    }

    pub fn merge_with_pending(&mut self, merge_key: &str, incoming: Vec<ParsedSentence>) -> Vec<ParsedSentence> {
        let mut pending = self.take_fragments(merge_key);
        pending.extend(incoming);
        pending.sort_by_key(|sentence| {
            sentence
                .fields
                .get(1)
                .and_then(|v| v.parse::<u32>().ok())
                .unwrap_or(0)
        });
        crate::session::reconcile::reconcile_fragments(pending)
    }
}

impl Default for PendingStore {
    fn default() -> Self {
        Self::new()
    }
}
""",
    )

    w(
        SRC / "export" / "mod.rs",
        """pub mod staging;
pub mod validate;
pub mod wrap;
pub mod writer;
""",
    )

    # BROKEN validate: noop
    w(
        SRC / "export" / "validate.rs",
        """use crate::model::MergeSnapshot;

/// BROKEN: skips talker-prefix validation.
pub fn validate_snapshot(_snapshot: &MergeSnapshot) -> Result<(), String> {
    Ok(())
}
""",
    )

    # BROKEN writer: unsorted digest
    w(
        SRC / "export" / "writer.rs",
        """use sha2::{Digest, Sha256};

use crate::model::MergeSnapshot;

/// BROKEN: digests unsorted groups as-is.
pub fn finalize_digest(snapshot: &mut MergeSnapshot) {
    let payload = serde_json::json!({
        "groups": snapshot.groups,
        "rejected": snapshot.rejected,
    });
    let bytes = serde_json::to_vec(&payload).unwrap_or_default();
    let digest = Sha256::digest(&bytes);
    snapshot.snapshot_digest = hex::encode(digest);
}

pub fn verify_digest(snapshot: &MergeSnapshot) -> Result<(), String> {
    let mut tmp = snapshot.clone();
    let claimed = tmp.snapshot_digest.clone();
    finalize_digest(&mut tmp);
    if tmp.snapshot_digest != claimed {
        return Err("digest mismatch".into());
    }
    Ok(())
}
""",
    )

    # BROKEN wrap: sorts by merge_key instead of stream order
    w(
        SRC / "export" / "wrap.rs",
        """use crate::model::{MergeReport, MergeSnapshot};

/// BROKEN: reorders groups by merge_key.
pub fn build_report(snapshot: &MergeSnapshot) -> MergeReport {
    let mut groups = snapshot.groups.clone();
    groups.sort_by(|a, b| a.merge_key.cmp(&b.merge_key));
    MergeReport {
        groups,
        rejected: snapshot.rejected.clone(),
        snapshot_digest: snapshot.snapshot_digest.clone(),
    }
}
""",
    )

    w(
        SRC / "export" / "staging.rs",
        """use std::fs;
use std::path::Path;

use crate::export::{validate, wrap, writer};
use crate::model::{MergeReport, MergeSnapshot};

pub fn write_snapshot(path: &Path, snapshot: &MergeSnapshot) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(snapshot).map_err(|e| e.to_string())?;
    fs::write(path, text).map_err(|e| e.to_string())
}

pub fn read_snapshot(path: &Path) -> Result<MergeSnapshot, String> {
    let text = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

pub fn publish_export(snapshot_path: &Path, output_path: &Path) -> Result<MergeReport, String> {
    let snapshot = read_snapshot(snapshot_path)?;
    writer::verify_digest(&snapshot)?;
    validate::validate_snapshot(&snapshot)?;
    let report = wrap::build_report(&snapshot);
    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?;
    fs::write(output_path, text).map_err(|e| e.to_string())?;
    Ok(report)
}
""",
    )

    w(
        SRC / "pipeline.rs",
        """use std::fs;
use std::path::Path;

use crate::context::rmc;
use crate::export::{staging, writer};
use crate::merge::compose;
use crate::model::{MergeSnapshot, RejectedLine};
use crate::parse::fields;
use crate::session::pending::PendingStore;
use crate::session::store::SessionState;

pub fn run_merge(input: &Path, output: &Path, state_path: Option<&Path>) -> Result<(), String> {
    let text = fs::read_to_string(input).map_err(|e| e.to_string())?;
    let use_session = state_path.is_some();
    let mut session = if let Some(p) = state_path {
        if p.exists() {
            let t = fs::read_to_string(p).map_err(|e| e.to_string())?;
            serde_json::from_str(&t).unwrap_or_default()
        } else {
            SessionState::default()
        }
    } else {
        SessionState::default()
    };

    let prev_date = session.rmc_date.clone();
    let mut pending = PendingStore::from_groups(session.pending.clone());
    let mut sentences = Vec::new();
    let mut rejected = Vec::new();
    for line in text.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        match fields::parse_line(line) {
            Ok(s) => {
                let date_before = session.rmc_date.clone();
                if rmc::update_rmc_context(&s, &mut session.rmc_date, &mut session.rmc_time) {
                    if use_session {
                        if let (Some(old), Some(new)) = (date_before.as_ref(), session.rmc_date.as_ref()) {
                            if old != new {
                                pending.clear_all();
                            }
                        } else if prev_date.is_some()
                            && session.rmc_date.is_some()
                            && prev_date.as_ref() != session.rmc_date.as_ref()
                        {
                            pending.clear_all();
                        }
                    }
                }
                sentences.push(s);
            }
            Err(reason) => rejected.push(RejectedLine {
                line: line.to_string(),
                reason,
            }),
        }
    }

    let mut result = compose::compose_stream(
        sentences,
        pending,
        session.rmc_date.clone(),
        session.rmc_time.clone(),
        use_session,
    );
    result.rejected.extend(rejected);
    session.rmc_date = result.rmc_date.clone();
    session.rmc_time = result.rmc_time.clone();

    // Attach UTC onto multipart groups using context
    for g in &mut result.groups {
        if g.utc_iso.is_none() {
            // leave None for multipart unless we have time in payload — skip
        }
    }

    let mut snapshot = MergeSnapshot {
        groups: result.groups,
        rejected: result.rejected,
        snapshot_digest: String::new(),
    };
    writer::finalize_digest(&mut snapshot);
    let snap_path = Path::new("/app/state/merge-snapshot.json");
    staging::write_snapshot(snap_path, &snapshot)?;
    staging::publish_export(snap_path, output)?;

    if let Some(p) = state_path {
        // Only persist buckets that include fragment one
        let mut groups = result.pending.into_groups();
        groups.retain(|g| g.fragments.iter().any(|f| f.fields.get(1).map(|v| v == "1").unwrap_or(false)));
        // BROKEN env pending may still stash orphans — filter on save in pipeline for session file contract when fixed pending is applied
        session.pending = groups;
        if let Some(parent) = p.parent() {
            fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        }
        let t = serde_json::to_string_pretty(&session).map_err(|e| e.to_string())?;
        fs::write(p, t).map_err(|e| e.to_string())?;
    }
    Ok(())
}
""",
    )

    w(
        SRC / "lib.rs",
        """pub mod checksum;
pub mod context;
pub mod export;
pub mod merge;
pub mod model;
pub mod parse;
pub mod pipeline;
pub mod session;
pub mod talker;
""",
    )

    w(
        SRC / "main.rs",
        """use std::path::PathBuf;

use clap::{Parser, Subcommand};
use nmeapipeline::pipeline;

#[derive(Parser)]
#[command(name = "nmeapipeline")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    Merge {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        output: PathBuf,
        #[arg(long)]
        state: Option<PathBuf>,
    },
}

fn main() {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Merge { input, output, state } => {
            if let Err(e) = pipeline::run_merge(&input, &output, state.as_deref()) {
                eprintln!("{e}");
                std::process::exit(1);
            }
        }
    }
}
""",
    )


def write_solution() -> None:
    # Golden correct implementations
    w(
        SOL / "files" / "checksum.rs",
        """pub fn verify_checksum(line: &str) -> bool {
    let Some(star) = line.rfind('*') else { return false; };
    if star + 3 > line.len() { return false; };
    if !line.starts_with('$') { return false; }
    let body = &line[1..star];
    let claimed = &line[star + 1..star + 3];
    let mut v = 0u8;
    for b in body.bytes() {
        v ^= b;
    }
    format!("{v:02X}").eq_ignore_ascii_case(claimed)
}

pub fn compute_checksum_body(body_after_dollar: &str) -> String {
    let mut v = 0u8;
    for b in body_after_dollar.bytes() {
        v ^= b;
    }
    format!("{v:02X}")
}
""",
    )

    w(
        SOL / "files" / "fields.rs",
        """use crate::checksum;
use crate::model::ParsedSentence;

pub fn parse_line(line: &str) -> Result<ParsedSentence, String> {
    let line = line.trim();
    if !line.starts_with('$') || !checksum::verify_checksum(line) {
        return Err("checksum".into());
    }
    let star = line.rfind('*').unwrap();
    let body = &line[1..star];
    let mut parts = split_fields(body);
    if parts.is_empty() {
        return Err("empty".into());
    }
    let addr = parts.remove(0);
    if addr.len() < 5 {
        return Err("addr".into());
    }
    let talker = addr[..2].to_string();
    let sentence = addr[2..].to_string();
    let is_multipart = matches!(sentence.as_str(), "GSV" | "GSA")
        && parts.len() >= 2
        && parts[0].parse::<u32>().ok().filter(|&t| t > 1).is_some();
    Ok(ParsedSentence {
        raw: line.to_string(),
        talker,
        sentence,
        fields: parts,
        is_multipart,
    })
}

fn split_fields(body: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    let mut in_quotes = false;
    let chars: Vec<char> = body.chars().collect();
    let mut i = 0;
    while i < chars.len() {
        let c = chars[i];
        if in_quotes {
            if c == '"' {
                if i + 1 < chars.len() && chars[i + 1] == '"' {
                    cur.push('"');
                    i += 2;
                    continue;
                }
                in_quotes = false;
                cur.push('"'); // preserve closing quote in field value? Contract: surrounding quotes preserved
                // Actually: surrounding quotes are preserved — open quote was pushed when entering.
                i += 1;
                continue;
            }
            cur.push(c);
            i += 1;
            continue;
        }
        if c == '"' {
            in_quotes = true;
            cur.push('"'); // preserve opening quote
            i += 1;
            continue;
        }
        if c == ',' {
            out.push(cur);
            cur = String::new();
            i += 1;
            continue;
        }
        cur.push(c);
        i += 1;
    }
    out.push(cur);
    out
}
""",
    )

    w(
        SOL / "files" / "normalize.rs",
        """pub fn canonical_talker(talker: &str) -> String {
    match talker {
        "GP" | "GN" => "GN".to_string(),
        other => other.to_string(),
    }
}
""",
    )

    w(
        SOL / "files" / "multipart.rs",
        """use crate::model::ParsedSentence;

pub fn merge_payload(fragments: &[ParsedSentence]) -> (u32, u32, Vec<String>) {
    let mut sorted = fragments.to_vec();
    sorted.sort_by_key(|s| s.fields.get(1).and_then(|v| v.parse::<u32>().ok()).unwrap_or(0));
    let total = sorted
        .first()
        .and_then(|s| s.fields.first())
        .and_then(|v| v.parse().ok())
        .unwrap_or(1);
    let mut payload = Vec::new();
    for s in &sorted {
        if s.fields.len() > 3 {
            payload.extend(s.fields[3..].iter().cloned());
        }
    }
    (total, sorted.len() as u32, payload)
}

pub fn merge_key(talker: &str, sentence: &str, total: u32) -> String {
    format!("{talker}:{sentence}:{total}")
}
""",
    )

    w(
        SOL / "files" / "datetime.rs",
        """pub fn attach_utc(rmc_date: Option<&str>, rmc_time: Option<&str>, time_field: &str) -> Option<String> {
    let date = rmc_date?;
    if date.len() != 6 {
        return None;
    }
    let mut day: u32 = date[0..2].parse().ok()?;
    let mut month: u32 = date[2..4].parse().ok()?;
    let mut year: u32 = 2000 + date[4..6].parse::<u32>().ok()?;
    let (hh, mm, ss) = parse_time(time_field)?;
    if let Some(rt) = rmc_time {
        if let Some((rh, _, _)) = parse_time(rt) {
            if hh < rh {
                day += 1;
                let dim = days_in_month(year, month);
                if day > dim {
                    day = 1;
                    month += 1;
                    if month > 12 {
                        month = 1;
                        year += 1;
                    }
                }
            }
        }
    }
    Some(format!("{year:04}-{month:02}-{day:02}T{hh:02}:{mm:02}:{ss:02}Z"))
}

fn parse_time(t: &str) -> Option<(u32, u32, u32)> {
    if t.len() < 6 {
        return None;
    }
    Some((t[0..2].parse().ok()?, t[2..4].parse().ok()?, t[4..6].parse().ok()?))
}

pub fn days_in_month(year: u32, month: u32) -> u32 {
    match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            if year % 4 == 0 && (year % 100 != 0 || year % 400 == 0) {
                29
            } else {
                28
            }
        }
        _ => 30,
    }
}
""",
    )

    w(
        SOL / "files" / "rmc.rs",
        """use crate::model::ParsedSentence;

pub fn update_rmc_context(
    sentence: &ParsedSentence,
    rmc_date: &mut Option<String>,
    rmc_time: &mut Option<String>,
) -> bool {
    if sentence.sentence != "RMC" || sentence.fields.len() < 9 {
        return false;
    }
    let status = sentence.fields.get(1).map(|s| s.as_str()).unwrap_or("");
    if status != "A" {
        return false;
    }
    let time = sentence.fields[0].clone();
    let date = sentence.fields[8].clone();
    if date.len() == 6 && time.len() >= 6 {
        *rmc_time = Some(time);
        *rmc_date = Some(date);
        return true;
    }
    false
}
""",
    )

    w(
        SOL / "files" / "reconcile.rs",
        """use std::collections::HashMap;

use crate::model::ParsedSentence;

/// When pending fragments merge with new input, duplicate message numbers keep the
/// fragment that arrived later in the combined pending-plus-input sequence.
pub fn reconcile_fragments(fragments: Vec<ParsedSentence>) -> Vec<ParsedSentence> {
    let mut by_num: HashMap<String, ParsedSentence> = HashMap::new();
    for sentence in fragments {
        let num = sentence
            .fields
            .get(1)
            .cloned()
            .unwrap_or_else(|| "0".to_string());
        by_num.insert(num, sentence);
    }
    let mut out: Vec<ParsedSentence> = by_num.into_values().collect();
    out.sort_by_key(|sentence| {
        sentence
            .fields
            .get(1)
            .and_then(|v| v.parse::<u32>().ok())
            .unwrap_or(0)
    });
    out
}
""",
    )

    w(
        SOL / "files" / "pending.rs",
        """use std::collections::HashMap;

use crate::merge::multipart;
use crate::model::{MergeGroup, ParsedSentence};
use crate::session::store::PendingGroup;

pub struct PendingStore {
    groups: HashMap<String, Vec<ParsedSentence>>,
}

impl PendingStore {
    pub fn new() -> Self {
        Self { groups: HashMap::new() }
    }

    pub fn from_groups(groups: Vec<PendingGroup>) -> Self {
        let mut map = HashMap::new();
        for group in groups {
            map.insert(group.merge_key, group.fragments);
        }
        Self { groups: map }
    }

    pub fn into_groups(self) -> Vec<PendingGroup> {
        self.groups
            .into_iter()
            .filter(|(_, fragments)| {
                fragments.iter().any(|f| f.fields.get(1).map(|v| v == "1").unwrap_or(false))
            })
            .map(|(merge_key, fragments)| {
                let first = fragments.first().cloned().unwrap_or(ParsedSentence {
                    raw: String::new(),
                    talker: String::new(),
                    sentence: String::new(),
                    fields: Vec::new(),
                    is_multipart: true,
                });
                let talker = crate::talker::normalize::canonical_talker(&first.talker);
                let sentence = first.sentence.clone();
                let multipart_total = first
                    .fields
                    .first()
                    .and_then(|v| v.parse().ok())
                    .unwrap_or(1);
                PendingGroup {
                    merge_key,
                    talker,
                    sentence,
                    multipart_total,
                    fragments,
                }
            })
            .collect()
    }

    pub fn clear_all(&mut self) {
        self.groups.clear();
    }

    pub fn is_empty(&self) -> bool {
        self.groups.is_empty()
    }

    pub fn take_fragments(&mut self, merge_key: &str) -> Vec<ParsedSentence> {
        self.groups.remove(merge_key).unwrap_or_default()
    }

    pub fn stash_incomplete(&mut self, merge_key: String, fragments: Vec<ParsedSentence>) {
        self.groups.insert(merge_key, fragments);
    }

    pub fn group_from_bucket(
        &self,
        merge_key: &str,
        fragments: &[ParsedSentence],
        emit_incomplete: bool,
    ) -> Option<MergeGroup> {
        if fragments.is_empty() {
            return None;
        }
        let first = &fragments[0];
        let talker = crate::talker::normalize::canonical_talker(&first.talker);
        let (multipart_total, fragments_merged, payload_fields) =
            multipart::merge_payload(fragments);
        if !emit_incomplete && fragments_merged < multipart_total {
            return None;
        }
        Some(MergeGroup {
            merge_key: merge_key.to_string(),
            talker,
            sentence: first.sentence.clone(),
            multipart_total,
            fragments_merged,
            payload_fields,
            utc_iso: None,
        })
    }

    pub fn finalize_bucket(
        &mut self,
        merge_key: String,
        fragments: Vec<ParsedSentence>,
        use_session: bool,
        out: &mut Vec<MergeGroup>,
    ) {
        if fragments.is_empty() {
            return;
        }
        let has_one = fragments
            .iter()
            .any(|f| f.fields.get(1).map(|v| v == "1").unwrap_or(false));
        if !has_one {
            // orphan drop
            return;
        }
        let total = fragments[0]
            .fields
            .first()
            .and_then(|v| v.parse::<u32>().ok())
            .unwrap_or(1);
        let merged = {
            let mut nums = std::collections::HashSet::new();
            for f in &fragments {
                if let Some(n) = f.fields.get(1) {
                    nums.insert(n.clone());
                }
            }
            nums.len() as u32
        };
        if use_session && merged < total {
            self.stash_incomplete(merge_key, fragments);
            return;
        }
        if let Some(group) = self.group_from_bucket(&merge_key, &fragments, true) {
            out.push(group);
        }
    }

    pub fn merge_with_pending(&mut self, merge_key: &str, incoming: Vec<ParsedSentence>) -> Vec<ParsedSentence> {
        let mut pending = self.take_fragments(merge_key);
        pending.extend(incoming);
        pending.sort_by_key(|sentence| {
            sentence
                .fields
                .get(1)
                .and_then(|v| v.parse::<u32>().ok())
                .unwrap_or(0)
        });
        crate::session::reconcile::reconcile_fragments(pending)
    }
}

impl Default for PendingStore {
    fn default() -> Self {
        Self::new()
    }
}
""",
    )

    w(
        SOL / "files" / "validate.rs",
        """use crate::model::MergeSnapshot;

pub fn validate_snapshot(snapshot: &MergeSnapshot) -> Result<(), String> {
    for group in &snapshot.groups {
        if !group.merge_key.starts_with(&format!("{}:", group.talker)) {
            return Err(format!(
                "merge_key {} must begin with canonical talker {}",
                group.merge_key, group.talker
            ));
        }
    }
    Ok(())
}
""",
    )

    w(
        SOL / "files" / "writer.rs",
        """use sha2::{Digest, Sha256};
use serde::Serialize;

use crate::model::{MergeGroup, MergeSnapshot, RejectedLine};

#[derive(Serialize)]
struct DigestPayload<'a> {
    groups: &'a [MergeGroup],
    rejected: &'a [RejectedLine],
}

pub fn finalize_digest(snapshot: &mut MergeSnapshot) {
    let mut groups = snapshot.groups.clone();
    let mut rejected = snapshot.rejected.clone();
    groups.sort_by(|a, b| a.merge_key.cmp(&b.merge_key));
    rejected.sort_by(|a, b| a.line.cmp(&b.line));
    let digest = digest_parts(&groups, &rejected);
    snapshot.snapshot_digest = digest;
}

pub fn verify_digest(snapshot: &MergeSnapshot) -> Result<(), String> {
    let mut groups = snapshot.groups.clone();
    let mut rejected = snapshot.rejected.clone();
    groups.sort_by(|a, b| a.merge_key.cmp(&b.merge_key));
    rejected.sort_by(|a, b| a.line.cmp(&b.line));
    let expected = digest_parts(&groups, &rejected);
    if expected != snapshot.snapshot_digest {
        return Err("digest mismatch".into());
    }
    Ok(())
}

fn digest_parts(groups: &[MergeGroup], rejected: &[RejectedLine]) -> String {
    // Typed serialize keeps declaration field order (json! alphabetizes keys).
    let bytes = serde_json::to_vec(&DigestPayload { groups, rejected }).unwrap_or_default();
    hex::encode(Sha256::digest(&bytes))
}
""",
    )

    w(
        SOL / "files" / "wrap.rs",
        """use crate::model::{MergeReport, MergeSnapshot};

pub fn build_report(snapshot: &MergeSnapshot) -> MergeReport {
    MergeReport {
        groups: snapshot.groups.clone(),
        rejected: snapshot.rejected.clone(),
        snapshot_digest: snapshot.snapshot_digest.clone(),
    }
}
""",
    )

    w(
        SOL / "files" / "compose.rs",
        """use std::collections::{HashMap, HashSet};

use crate::merge::{datetime, multipart};
use crate::model::{MergeGroup, ParsedSentence, RejectedLine};
use crate::session::pending::PendingStore;
use crate::talker::normalize;

pub struct ComposeResult {
    pub groups: Vec<MergeGroup>,
    pub rejected: Vec<RejectedLine>,
    pub rmc_date: Option<String>,
    pub rmc_time: Option<String>,
    pub pending: PendingStore,
}

pub fn compose_stream(
    sentences: Vec<ParsedSentence>,
    mut pending: PendingStore,
    rmc_date: Option<String>,
    rmc_time: Option<String>,
    use_session: bool,
) -> ComposeResult {
    let mut buckets: HashMap<String, Vec<ParsedSentence>> = HashMap::new();
    let mut order: Vec<String> = Vec::new();
    let mut single_map: HashMap<String, MergeGroup> = HashMap::new();

    for s in sentences {
        if s.is_multipart {
            let talker = normalize::canonical_talker(&s.talker);
            let total = s.fields.first().and_then(|v| v.parse().ok()).unwrap_or(1);
            let key = multipart::merge_key(&talker, &s.sentence, total);
            if !buckets.contains_key(&key) {
                order.push(key.clone());
                let prior = pending.take_fragments(&key);
                buckets.insert(key.clone(), prior);
            }
            buckets.get_mut(&key).unwrap().push(s);
        } else {
            let talker = normalize::canonical_talker(&s.talker);
            let key = format!("{talker}:{}:1", s.sentence);
            let utc = s.fields.first().and_then(|t| {
                datetime::attach_utc(rmc_date.as_deref(), rmc_time.as_deref(), t)
            });
            if !order.contains(&key) {
                order.push(key.clone());
            }
            single_map.insert(
                key.clone(),
                MergeGroup {
                    merge_key: key,
                    talker,
                    sentence: s.sentence.clone(),
                    multipart_total: 1,
                    fragments_merged: 1,
                    payload_fields: s.fields.clone(),
                    utc_iso: utc,
                },
            );
        }
    }

    let mut groups = Vec::new();
    let mut emitted = HashSet::new();
    for key in &order {
        if let Some(frags) = buckets.remove(key) {
            let combined = pending.merge_with_pending(key, frags);
            pending.finalize_bucket(key.clone(), combined, use_session, &mut groups);
            emitted.insert(key.clone());
        } else if let Some(g) = single_map.get(key) {
            groups.push(g.clone());
            emitted.insert(key.clone());
        }
    }

    ComposeResult {
        groups,
        rejected: Vec::new(),
        rmc_date,
        rmc_time,
        pending,
    }
}
""",
    )

    w(
        SOL / "files" / "staging.rs",
        """use std::fs;
use std::path::Path;

use crate::export::{validate, wrap, writer};
use crate::model::{MergeReport, MergeSnapshot};

pub fn write_snapshot(path: &Path, snapshot: &MergeSnapshot) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(snapshot).map_err(|e| e.to_string())?;
    fs::write(path, text).map_err(|e| e.to_string())
}

pub fn read_snapshot(path: &Path) -> Result<MergeSnapshot, String> {
    let text = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

pub fn publish_export(snapshot_path: &Path, output_path: &Path) -> Result<MergeReport, String> {
    let snapshot = read_snapshot(snapshot_path)?;
    writer::verify_digest(&snapshot)?;
    validate::validate_snapshot(&snapshot)?;
    let report = wrap::build_report(&snapshot);
    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let text = serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?;
    fs::write(output_path, text).map_err(|e| e.to_string())?;
    Ok(report)
}
""",
    )

    # Also copy goldens for verifier-golden naming used by tests
    for name in [
        "checksum.rs",
        "fields.rs",
        "normalize.rs",
        "multipart.rs",
        "datetime.rs",
        "rmc.rs",
        "reconcile.rs",
        "pending.rs",
        "validate.rs",
        "writer.rs",
        "wrap.rs",
        "compose.rs",
        "staging.rs",
    ]:
        content = (SOL / "files" / name).read_text(encoding="utf-8")
        w(SOL / f"golden_{name}", content)
        w(TESTS / "verifier-golden" / name, content)

    # Broken copies for partial probes
    for name, src in [
        ("checksum.rs", SRC / "checksum.rs"),
        ("reconcile.rs", SRC / "session" / "reconcile.rs"),
        ("validate.rs", SRC / "export" / "validate.rs"),
        ("pending.rs", SRC / "session" / "pending.rs"),
        ("staging.rs", SRC / "export" / "staging.rs"),
        ("multipart.rs", SRC / "merge" / "multipart.rs"),
        ("compose.rs", SRC / "merge" / "compose.rs"),
        ("writer.rs", SRC / "export" / "writer.rs"),
        ("wrap.rs", SRC / "export" / "wrap.rs"),
        ("normalize.rs", SRC / "talker" / "normalize.rs"),
        ("accumulate.rs", SRC / "merge" / "accumulate.rs"),
    ]:
        w(TESTS / "verifier-broken" / name, src.read_text(encoding="utf-8"))

    w(
        SOL / "solve.sh",
        """#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cargo/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution" "/task/solution"; do
  if [[ -f "${candidate}/files/checksum.rs" ]]; then
    SOL_DIR="${candidate}"
    break
  fi
done
[[ -n "${SOL_DIR}" ]] || { echo "solution/files/checksum.rs not found" >&2; exit 1; }

F="${SOL_DIR}/files"
cp -f "${F}/checksum.rs" /app/crates/nmeapipeline/src/checksum.rs
cp -f "${F}/fields.rs" /app/crates/nmeapipeline/src/parse/fields.rs
cp -f "${F}/normalize.rs" /app/crates/nmeapipeline/src/talker/normalize.rs
cp -f "${F}/multipart.rs" /app/crates/nmeapipeline/src/merge/multipart.rs
cp -f "${F}/datetime.rs" /app/crates/nmeapipeline/src/merge/datetime.rs
cp -f "${F}/compose.rs" /app/crates/nmeapipeline/src/merge/compose.rs
cp -f "${F}/rmc.rs" /app/crates/nmeapipeline/src/context/rmc.rs
cp -f "${F}/reconcile.rs" /app/crates/nmeapipeline/src/session/reconcile.rs
cp -f "${F}/pending.rs" /app/crates/nmeapipeline/src/session/pending.rs
cp -f "${F}/validate.rs" /app/crates/nmeapipeline/src/export/validate.rs
cp -f "${F}/writer.rs" /app/crates/nmeapipeline/src/export/writer.rs
cp -f "${F}/wrap.rs" /app/crates/nmeapipeline/src/export/wrap.rs
cp -f "${F}/staging.rs" /app/crates/nmeapipeline/src/export/staging.rs

find /app/crates -name '*.rs' -exec sed -i 's/\\r$//' {} +

cargo build --release --locked -p nmeapipeline
install -m 0755 /app/target/release/nmeapipeline /usr/local/bin/nmeapipeline
bash /app/scripts/reset-state.sh
nmeapipeline merge --input /app/fixtures/streams/baseline.nmea --output /app/output/merge-report.json
""",
    )


def write_tests(nmea_line) -> None:
    w(
        TESTS / "test.sh",
        """#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /app/output /app/state
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

set +e
bash /app/scripts/reset-state.sh
RESET_RC=$?
cargo build --release --locked -p nmeapipeline
BUILD_RC=$?
install -m 0755 /app/target/release/nmeapipeline /usr/local/bin/nmeapipeline
INSTALL_RC=$?
[ "$RESET_RC" -eq 0 ] && [ "$BUILD_RC" -eq 0 ] && [ "$INSTALL_RC" -eq 0 ] && \\
  /opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \\
    --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
""",
    )
    part2 = TESTS / "hidden_bundles" / "duplicate-replay-part2.nmea"
    if not part2.exists():
        w(
            part2,
            "\n".join(
                [
                    nmea_line("$GPGSV,2,1,08,22,50,090,50,05,20,310,44"),
                    nmea_line("$GNGSV,2,2,08,33,06,122,42,04,12,311,43"),
                ]
            )
            + "\n",
        )


if __name__ == "__main__":
    main()
