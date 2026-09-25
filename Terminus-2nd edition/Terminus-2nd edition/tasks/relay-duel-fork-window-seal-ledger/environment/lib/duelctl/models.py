"""JSON shapes for duel ledger staging, score, and publish seal (dict contracts)."""

from __future__ import annotations

from typing import Any, TypedDict


class Message(TypedDict, total=False):
    ts_ms: int
    direction: str
    method: str
    duel_id: str
    lane_tag: str
    fork_tag: str
    cseq: int
    status: int
    branch_id: str


class ScoreWindow(TypedDict):
    name: str
    start_minute: int
    end_minute: int
    tier: str


class Policy(TypedDict, total=False):
    clock_skew_ms: int
    windows: list[ScoreWindow]


class Match(TypedDict, total=False):
    duel_id: str
    branch_key: str
    answer_ts_ms: int
    end_ts_ms: int
    disposition: str
    answered: bool
    score_band: str
    duration_sec: float


class MatchBuffer(TypedDict, total=False):
    arena: str
    scenario: str
    messages: list[dict[str, Any]]
    policy: dict[str, Any]
    matches: dict[str, dict[str, Any]]
    match_seal: str


class ScoreReport(TypedDict):
    arena: str
    scenario: str
    rated_count: int
    window_hits: int


class PublishSeal(TypedDict):
    match_seal: str
    row_count: int
    score_epoch: int
