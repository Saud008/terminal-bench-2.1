"""Reference transaction-state machine for payment terminal batch settlement."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any


def _read_batch(scenario: str, fixture_root: Path) -> dict[str, Any]:
    return json.loads((fixture_root / "scenarios" / f"{scenario}.json").read_text(encoding="utf-8"))


def _auth_lower(code: str) -> str:
    return code.lower()


def _bootstrap_row(txn: dict[str, Any]) -> dict[str, Any]:
    if txn["txn_type"] == "sale":
        state = "captured"
    elif txn["txn_type"] == "reversal":
        state = "reversal_pending"
    else:
        state = "unknown"
    row = dict(txn)
    row["auth_code_norm"] = _auth_lower(txn["auth_code"])
    row["state"] = state
    return row


def _link_key(terminal: str, auth: str, sale_id: str) -> str:
    return f"{terminal}|{auth}|{sale_id}"


def _apply_reversal_links(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = [dict(r) for r in rows]
    sale_idx: dict[str, int] = {}
    for idx, row in enumerate(out):
        if row["txn_type"] != "sale":
            continue
        sale_idx[_link_key(row["terminal_id"], row["auth_code_norm"], row["txn_id"])] = idx
    for idx, row in enumerate(out):
        if row["txn_type"] != "reversal":
            continue
        key = _link_key(row["terminal_id"], row["auth_code_norm"], row["links_sale_id"])
        if key in sale_idx and out[sale_idx[key]]["amount_cents"] == row["amount_cents"]:
            out[idx]["state"] = "reversal_applied"
            out[sale_idx[key]]["state"] = "settled"
        else:
            out[idx]["state"] = "reversal_rejected"
    return out


def _within_cutoff(rows: list[dict[str, Any]], cutoff_ms: int) -> list[dict[str, Any]]:
    return [r for r in rows if r["event_ms"] <= cutoff_ms]


def _order_by_event(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: (r["event_ms"], r["txn_id"]))


def _digest_line(
    batch_id: str,
    terminal_id: str,
    merchant_id: str,
    txn_id: str,
    auth_norm: str,
    amount: int,
    state: str,
) -> str:
    material = "|".join(
        [batch_id, terminal_id, merchant_id, txn_id, auth_norm, str(amount), state]
    )
    return hashlib.sha256(material.encode()).hexdigest()


def _finalize_captured_sales(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = [dict(r) for r in rows]
    for row in out:
        if row["txn_type"] == "sale" and row["state"] == "captured":
            row["state"] = "settled"
    return out


def expected_journal_rows(scenario: str, fixture_root: Path) -> list[dict[str, Any]]:
    batch = _read_batch(scenario, fixture_root)
    staged = [_bootstrap_row(t) for t in batch["transcripts"]]
    linked = _apply_reversal_links(staged)
    finalized = _finalize_captured_sales(linked)
    bounded = _within_cutoff(finalized, batch["cutoff_event_ms"])
    ordered = _order_by_event(bounded)
    lines: list[dict[str, Any]] = []
    for seq, row in enumerate(ordered, start=1):
        lines.append(
            {
                "seq": seq,
                "txn_id": row["txn_id"],
                "terminal_id": row["terminal_id"],
                "merchant_id": row["merchant_id"],
                "txn_type": row["txn_type"],
                "amount_cents": row["amount_cents"],
                "state": row["state"],
                "normalized_digest": _digest_line(
                    batch["batch_id"],
                    row["terminal_id"],
                    row["merchant_id"],
                    row["txn_id"],
                    row["auth_code_norm"],
                    row["amount_cents"],
                    row["state"],
                ),
            }
        )
    return lines


def _canonical_line_bytes(line: dict[str, Any]) -> str:
    ordered = {
        "seq": line["seq"],
        "txn_id": line["txn_id"],
        "terminal_id": line["terminal_id"],
        "merchant_id": line["merchant_id"],
        "txn_type": line["txn_type"],
        "amount_cents": line["amount_cents"],
        "state": line["state"],
        "normalized_digest": line["normalized_digest"],
    }
    return json.dumps(ordered, separators=(",", ":"))


def digest_journal_lines(lines: list[dict[str, Any]]) -> str:
    body = [_canonical_line_bytes(line) for line in lines]
    payload = "\n".join(body) + ("\n" if body else "")
    return hashlib.sha256(payload.encode()).hexdigest()


def expected_journal_header(scenario: str, fixture_root: Path) -> dict[str, Any]:
    batch = _read_batch(scenario, fixture_root)
    lines = expected_journal_rows(scenario, fixture_root)
    return {
        "engine": "termsetctl",
        "scenario": scenario,
        "batch_id": batch["batch_id"],
        "journal_digest": digest_journal_lines(lines),
        "line_count": len(lines),
    }


def _derive_terminal_key(scenario: str, fixture_root: Path) -> str:
    batch = _read_batch(scenario, fixture_root)
    if "terminal_key_hex" in batch:
        return batch["terminal_key_hex"]
    salt = os.environ.get("TB3_TERMINAL_KEY_SALT", "")
    return hashlib.sha256(f"termset-key:{scenario}:{salt}".encode()).hexdigest()


def expected_bundle_payload(scenario: str, fixture_root: Path) -> dict[str, Any]:
    batch = _read_batch(scenario, fixture_root)
    lines = expected_journal_rows(scenario, fixture_root)
    j_digest = digest_journal_lines(lines)
    net = 0
    settled = 0
    for line in lines:
        if line["state"] == "settled":
            net += line["amount_cents"]
            settled += 1
        elif line["state"] == "reversal_applied":
            net -= line["amount_cents"]
    return {
        "engine": "termsetctl",
        "scenario": scenario,
        "batch_id": batch["batch_id"],
        "terminal_key_id": batch["terminal_key_id"],
        "journal_digest": j_digest,
        "net_amount_cents": net,
        "settled_count": settled,
        "bundle_version": 1,
    }


def expected_hmac_witness(scenario: str, fixture_root: Path) -> str:
    bundle = expected_bundle_payload(scenario, fixture_root)
    key = bytes.fromhex(_derive_terminal_key(scenario, fixture_root))
    return hmac.new(key, bundle["journal_digest"].encode(), hashlib.sha256).hexdigest()
