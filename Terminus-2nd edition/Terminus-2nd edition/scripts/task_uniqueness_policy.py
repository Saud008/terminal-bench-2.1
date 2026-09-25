#!/usr/bin/env python3
"""Task uniqueness policy — similarity gate + pack distinct-dimension checks.

Policy: archive/terminus-rules-mdc/shared/task-uniqueness-gate.mdc
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- Forbidden similarity / spam classes (ideas + pack) ---
SIMILARITY_RULES: tuple[tuple[str, str], ...] = (
    ("no_duplicate", "No duplicate tasks"),
    ("no_copy", "No copy tasks"),
    ("no_sibling", "No sibling tasks"),
    ("no_same_family", "No same-family tasks"),
    ("no_same_lane", "No same-lane tasks"),
    ("no_template_variant", "No template-generated variants"),
    ("no_fabricated_benchmark", "No fabricated benchmark-style problems"),
    ("no_synthetic_puzzle", "No synthetic puzzle tasks"),
    ("no_spam", "No spam submissions"),
)

DISTINCT_RULES: tuple[tuple[str, str], ...] = (
    ("distinct_workflow", "Distinct real-world workflow"),
    ("distinct_artifact", "Distinct primary artifact"),
    ("distinct_reasoning", "Distinct reasoning pattern"),
    ("distinct_objective", "Distinct operational objective"),
    ("distinct_industry", "Distinct industry use case"),
)

CLASS_TO_RULE: dict[str, str] = {
    "DUPLICATE": "no_duplicate",
    "COPY": "no_copy",
    "SIBLING": "no_sibling",
    "FAMILY": "no_same_family",
    "SAME_LANE": "no_same_lane",
    "TEMPLATED": "no_template_variant",
    "FABRICATED": "no_fabricated_benchmark",
    "SYNTHETIC": "no_synthetic_puzzle",
}

GENERIC_DOMAINS = frozenset(
    {
        "go",
        "rust",
        "python",
        "java",
        "bash",
        "node",
        "typescript",
        "task",
        "cli",
        "general",
        "misc",
        "other",
        "engineering",
        "software",
    }
)

ARTIFACT_KEYWORDS = (
    "report",
    "ledger",
    "snapshot",
    "manifest",
    "atlas",
    "graph",
    "topology",
    "bundle",
    "seal",
    "certificate",
    "registry",
    "catalog",
    "index",
    "archive",
    "packet",
    "frame",
    "trace",
    "timeline",
    "rollup",
    "receipt",
    "attestation",
    "provenance",
    "schema",
    "export",
    "json",
    "jsonl",
    "csv",
    "sqlite",
    "wal",
    "tar",
    "binary",
    "protobuf",
    "parquet",
)

WORKFLOW_KEYWORDS = (
    "ingest",
    "export",
    "staging",
    "analyze",
    "correlate",
    "attest",
    "govern",
    "reconstruct",
    "normalize",
    "merge",
    "replay",
    "audit",
    "validate",
    "compile",
    "build",
    "generate",
    "derive",
    "reconcile",
    "classify",
    "decode",
    "encode",
    "transform",
    "orchestrate",
    "publish",
    "materialize",
)

REASONING_KEYWORDS = (
    "provenance",
    "lineage",
    "checksum",
    "epoch",
    "closure",
    "constraint",
    "invariant",
    "idempot",
    "deterministic",
    "canonical",
    "ordering",
    "causal",
    "temporal",
    "spatial",
    "geodesy",
    "cryptographic",
    "consensus",
    "quorum",
    "dedupe",
    "witness",
    "merkle",
    "hash",
    "signature",
    "policy",
    "compliance",
)

OBJECTIVE_VERBS = (
    "build",
    "analyze",
    "implement",
    "construct",
    "derive",
    "reconstruct",
    "correlate",
    "govern",
    "attest",
    "materialize",
    "produce",
    "generate",
    "compile",
    "orchestrate",
    "establish",
    "validate",
    "classify",
    "normalize",
)

FABRICATED_PATTERNS = (
    re.compile(r"\bbenchmark[- ]style\b", re.I),
    re.compile(r"\bfabricated benchmark\b", re.I),
    re.compile(r"\bsynthetic benchmark\b", re.I),
    re.compile(r"\bcontrived benchmark\b", re.I),
)

SYNTHETIC_PATTERNS = (
    re.compile(r"\bsynthetic puzzle\b", re.I),
    re.compile(r"\bpuzzle task\b", re.I),
    re.compile(r"\bbrain\s*teaser\b", re.I),
    re.compile(r"\btoy problem\b", re.I),
    re.compile(r"\bleetcode\b", re.I),
    re.compile(r"\binterview puzzle\b", re.I),
)

OUTPUT_PATH_RE = re.compile(r"/app/(?:output|state|docs)[/\w.\-]+")


@dataclass
class UniquenessReport:
    checks: dict[str, str] = field(default_factory=dict)
    violations: list[str] = field(default_factory=list)
    verdict: str = "PASS"

    def record(self, check_id: str, status: str, detail: str = "") -> None:
        self.checks[check_id] = status
        if status == "FAIL" and detail:
            self.violations.append(f"{check_id}: {detail}")

    def finalize(self) -> None:
        self.verdict = "FAIL" if any(s == "FAIL" for s in self.checks.values()) else "PASS"


def _blob_lower(*parts: str) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip()).lower()


def _blocker_blob(blockers: list[str]) -> str:
    return " ".join(blockers).lower()


def audit_similarity_rules(
    *,
    unacceptable_classes: list[str] | None = None,
    blockers: list[str] | None = None,
    weighted: float = 0.0,
    idea_threshold: float = 0.10,
) -> dict[str, str]:
    """Map anti-spam / unacceptable classes to uniqueness similarity rules."""
    classes = set(unacceptable_classes or [])
    blockers = blockers or []
    bb = _blocker_blob(blockers)
    out: dict[str, str] = {}

    for rule_id, _label in SIMILARITY_RULES:
        out[rule_id] = "PASS"

    for cls, rule_id in CLASS_TO_RULE.items():
        if cls in classes:
            out[rule_id] = "FAIL"

    if "slug already exists" in bb or "near-duplicate slug" in bb:
        out["no_duplicate"] = "FAIL"
    if "idea similarity blocked" in bb or weighted > idea_threshold:
        out["no_template_variant"] = "FAIL"
        if weighted > idea_threshold and "COPY" not in classes:
            out["no_copy"] = "FAIL"
    if "family saturation" in bb:
        out["no_same_family"] = "FAIL"
        out["no_same_lane"] = "FAIL"
    if "spam slug pattern" in bb:
        out["no_spam"] = "FAIL"

    return out


def audit_distinct_dimensions(
    *,
    domain: str = "",
    title: str = "",
    summary: str = "",
    instruction: str = "",
    tags: tuple[str, ...] = (),
) -> dict[str, str]:
    """Require five distinct dimensions in idea text or built instruction."""
    blob = _blob_lower(domain, title, summary, instruction, " ".join(tags))
    domain_norm = domain.strip().lower()
    out: dict[str, str] = {}

    # Industry / use case
    industry_ok = (
        len(domain_norm) >= 4
        and domain_norm not in GENERIC_DOMAINS
        and not re.fullmatch(r"[a-z]{2,4}", domain_norm)
    )
    if not industry_ok and tags:
        industry_ok = any(len(t) >= 4 and t.lower() not in GENERIC_DOMAINS for t in tags)
    out["distinct_industry"] = "PASS" if industry_ok else "FAIL"

    artifact_ok = any(kw in blob for kw in ARTIFACT_KEYWORDS) or bool(
        OUTPUT_PATH_RE.search(instruction or summary)
    )
    out["distinct_artifact"] = "PASS" if artifact_ok else "FAIL"

    workflow_ok = any(kw in blob for kw in WORKFLOW_KEYWORDS)
    out["distinct_workflow"] = "PASS" if workflow_ok else "FAIL"

    reasoning_ok = any(kw in blob for kw in REASONING_KEYWORDS)
    out["distinct_reasoning"] = "PASS" if reasoning_ok else "FAIL"

    objective_ok = (
        len(summary.strip()) >= 35 or len(instruction.strip()) >= 80
    ) and any(v in blob for v in OBJECTIVE_VERBS)
    out["distinct_objective"] = "PASS" if objective_ok else "FAIL"

    return out


def audit_fabricated_synthetic_text(text: str) -> dict[str, str]:
    out = {"no_fabricated_benchmark": "PASS", "no_synthetic_puzzle": "PASS"}
    for pat in FABRICATED_PATTERNS:
        if pat.search(text):
            out["no_fabricated_benchmark"] = "FAIL"
            break
    for pat in SYNTHETIC_PATTERNS:
        if pat.search(text):
            out["no_synthetic_puzzle"] = "FAIL"
            break
    return out


def build_idea_uniqueness_report(
    *,
    unacceptable_classes: list[str] | None = None,
    blockers: list[str] | None = None,
    warnings: list[str] | None = None,
    weighted: float = 0.0,
    domain: str = "",
    title: str = "",
    summary: str = "",
    idea_threshold: float = 0.10,
) -> UniquenessReport:
    report = UniquenessReport()
    sim = audit_similarity_rules(
        unacceptable_classes=unacceptable_classes,
        blockers=blockers,
        weighted=weighted,
        idea_threshold=idea_threshold,
    )
    distinct = audit_distinct_dimensions(domain=domain, title=title, summary=summary)
    fab = audit_fabricated_synthetic_text(_blob_lower(title, summary, domain))

    merged: dict[str, str] = {}
    merged.update(sim)
    merged.update(fab)
    for k, v in distinct.items():
        merged[k] = v

    for check_id, status in merged.items():
        detail = ""
        if status == "FAIL":
            if check_id in dict(SIMILARITY_RULES):
                detail = dict(SIMILARITY_RULES)[check_id]
            elif check_id in dict(DISTINCT_RULES):
                detail = dict(DISTINCT_RULES)[check_id]
        report.record(check_id, status, detail)

    report.finalize()
    return report


def format_uniqueness_table(report: UniquenessReport) -> str:
    lines = ["| Check | PASS / FAIL |", "|-------|-------------|"]
    for rule_id, label in SIMILARITY_RULES + DISTINCT_RULES:
        status = report.checks.get(rule_id, "SKIP")
        lines.append(f"| {label} | {status} |")
    lines.append(f"| **Verdict** | **{report.verdict}** |")
    return "\n".join(lines)
