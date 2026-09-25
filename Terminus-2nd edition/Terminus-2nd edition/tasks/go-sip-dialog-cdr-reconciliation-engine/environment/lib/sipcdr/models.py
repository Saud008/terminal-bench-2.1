"""JSON shapes for SIP CDR staging, billing, and publish seal (dict contracts)."""

from __future__ import annotations

from typing import Any, TypedDict


class Message(TypedDict, total=False):
    ts_ms: int
    direction: str
    method: str
    call_id: str
    from_tag: str
    to_tag: str
    cseq: int
    status: int
    branch_id: str


class BillingWindow(TypedDict):
    name: str
    start_minute: int
    end_minute: int
    tier: str


class Policy(TypedDict, total=False):
    clock_skew_ms: int
    windows: list[BillingWindow]


class Dialog(TypedDict, total=False):
    call_id: str
    branch_key: str
    answer_ts_ms: int
    end_ts_ms: int
    disposition: str
    answered: bool
    billing_tier: str
    duration_sec: float


class DialogBuffer(TypedDict, total=False):
    tenant: str
    scenario: str
    messages: list[dict[str, Any]]
    policy: dict[str, Any]
    dialogs: dict[str, dict[str, Any]]
    dialog_seal: str


class BillingReport(TypedDict):
    tenant: str
    scenario: str
    rated_count: int
    window_hits: int


class PublishSeal(TypedDict):
    dialog_seal: str
    row_count: int
    billing_epoch: int
