"""Independent HMAC continuity witness refmath for livattest attest gate."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field

GRACE_MS = 5000
SKEW_TOLERANCE_MS = 2000
VAULT_KEY_HEX = (
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)


@dataclass
class Beat:
    seq: int
    client_ms: int


@dataclass
class Breach:
    from_seq: int
    to_seq: int
    missing_span: int
    opened_mono: int
    repaired: set[int] = field(default_factory=set)
    closed: bool = False


@dataclass
class ChainModel:
    token: str
    session_id: str
    anchor_client: int
    anchor_mono: int
    admission_ticket: str = ""
    last_seq: int | None = None
    breaches_opened: int = 0
    breaches_closed: int = 0
    missing_span_total: int = 0
    repair_events: int = 0
    active_ban: bool = False
    open_breach: Breach | None = None
    skew_rejections: int = 0
    duplicate_rejections: int = 0
    ticket_rejections: int = 0
    accepted: set[int] = field(default_factory=set)
    witness_seq: int = 0
    witness_head: str = ""
    prev_head: str = ""

    def mint_ticket(self) -> str:
        key = bytes.fromhex(VAULT_KEY_HEX)
        msg = f"{self.token}:{self.session_id}:{self.anchor_mono}".encode()
        self.admission_ticket = hmac.new(key, msg, hashlib.sha256).hexdigest()
        return self.admission_ticket

    def bind(self, client_ms: int, mono_ms: int) -> str:
        self.anchor_client = client_ms
        self.anchor_mono = mono_ms
        return self.mint_ticket()

    def _skew(self, client_ms: int, mono_ms: int) -> int:
        return abs((client_ms - self.anchor_client) - (mono_ms - self.anchor_mono))

    @staticmethod
    def _in_span(from_seq: int, to_seq: int, seq: int) -> bool:
        from_seq &= 0xFFFFFFFF
        to_seq &= 0xFFFFFFFF
        seq &= 0xFFFFFFFF
        if from_seq <= to_seq:
            return from_seq <= seq <= to_seq
        return seq >= from_seq or seq <= to_seq

    def _stage_witness(self) -> None:
        self.witness_seq += 1
        last = 0 if self.last_seq is None else self.last_seq
        msg = (
            f"{self.prev_head}:{self.token}:{self.session_id}:{last}:{self.witness_seq}"
        )
        self.witness_head = hashlib.sha256(msg.encode()).hexdigest()
        self.prev_head = self.witness_head

    def ingest(self, beat: Beat, mono_ms: int, ticket: str | None = None) -> str | None:
        if ticket is None:
            ticket = self.admission_ticket
        if ticket != self.admission_ticket:
            self.ticket_rejections += 1
            return "ticket"
        if self._skew(beat.client_ms, mono_ms) > SKEW_TOLERANCE_MS:
            self.skew_rejections += 1
            return "skew"

        seq = beat.seq & 0xFFFFFFFF

        # Repair first
        if self.open_breach is not None and not self.open_breach.closed:
            b = self.open_breach
            if self._in_span(b.from_seq, b.to_seq, seq) and seq not in b.repaired:
                b.repaired.add(seq)
                self.repair_events += 1
                self.accepted.add(seq)
                if len(b.repaired) >= b.missing_span:
                    b.closed = True
                    self.breaches_closed += 1
                    if mono_ms - b.opened_mono <= GRACE_MS:
                        self.active_ban = False
                    self.open_breach = None
                self._stage_witness()
                return None

        if seq in self.accepted:
            self.duplicate_rejections += 1
            return "duplicate"

        if self.last_seq is None:
            self.last_seq = seq
            self.accepted.add(seq)
            self._stage_witness()
            return None

        next_seq = (self.last_seq + 1) & 0xFFFFFFFF
        if seq == next_seq:
            self.last_seq = seq
            self.accepted.add(seq)
            self._stage_witness()
            return None

        from_seq = next_seq
        to_seq = (seq - 1) & 0xFFFFFFFF
        span = (seq - next_seq) & 0xFFFFFFFF
        self.open_breach = Breach(
            from_seq=from_seq,
            to_seq=to_seq,
            missing_span=span,
            opened_mono=mono_ms,
        )
        self.breaches_opened += 1
        self.missing_span_total += span
        self.active_ban = True
        self.last_seq = seq
        self.accepted.add(seq)
        self._stage_witness()
        return None

    def export(self) -> dict:
        report = {
            "token": self.token,
            "session_id": self.session_id,
            "last_seq": 0 if self.last_seq is None else self.last_seq,
            "breaches_opened": self.breaches_opened,
            "breaches_closed": self.breaches_closed,
            "missing_span_total": self.missing_span_total,
            "repair_events": self.repair_events,
            "active_ban_seals": 1 if self.active_ban else 0,
            "skew_rejections": self.skew_rejections,
            "duplicate_rejections": self.duplicate_rejections,
            "ticket_rejections": self.ticket_rejections,
            "witness_seq": self.witness_seq,
            "witness_head": self.witness_head,
        }
        canonical = json.dumps(report, sort_keys=True, separators=(",", ":"))
        report["audit_digest"] = hashlib.sha256(canonical.encode()).hexdigest()
        return report


def seed_mix(seed: str, label: str) -> int:
    digest = hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()
    return int(digest[:8], 16)


def derive_token(base: str, seed: str, scenario: str) -> str:
    return f"{base}-{seed_mix(seed, scenario) & 0xFFFF:04x}"


def derive_session_id(base: str, seed: str, scenario: str) -> str:
    return f"{base}-{seed_mix(seed, scenario + ':sess') & 0xFFFF:04x}"


def scenario_discontinuity_span(seed: str) -> ChainModel:
    token = derive_token("player", seed, "linear")
    session = derive_session_id("sess-a", seed, "linear")
    base_ms = 10000 + (seed_mix(seed, "linear:ms") % 500)
    mono = [0, 500, 1500, 2000, 2500]
    m = ChainModel(token, session, base_ms, mono[0])
    m.bind(base_ms, mono[0])
    beats = [
        Beat(1, base_ms + 0),
        Beat(4, base_ms + 1200),
        Beat(2, base_ms + 400),
        Beat(3, base_ms + 800),
    ]
    for beat, mono_ms in zip(beats, mono[1:], strict=True):
        assert m.ingest(beat, mono_ms) is None
    return m


def scenario_uint32_wrap_edge(seed: str) -> ChainModel:
    token = derive_token("player", seed, "wrap")
    session = derive_session_id("sess-wrap", seed, "wrap")
    base_ms = 50000 + (seed_mix(seed, "wrap:ms") % 200)
    mono = [0, 100, 200, 300, 400]
    m = ChainModel(token, session, base_ms, mono[0])
    m.bind(base_ms, mono[0])
    beats = [
        Beat(4294967294, base_ms + 0),
        Beat(4294967295, base_ms + 100),
        Beat(0, base_ms + 200),
        Beat(1, base_ms + 300),
    ]
    for beat, mono_ms in zip(beats, mono[1:], strict=True):
        assert m.ingest(beat, mono_ms) is None
    return m


def scenario_ticket_rebind(seed: str) -> tuple[ChainModel, ChainModel]:
    token = derive_token("player", seed, "rebind")
    old_sess = derive_session_id("sess-old", seed, "rebind")
    new_sess = derive_session_id("sess-new", seed, "rebind:new")
    base_ms = 20000 + (seed_mix(seed, "rebind:ms") % 300)
    mono = [0, 100, 200, 300, 400]

    old = ChainModel(token, old_sess, base_ms, mono[0])
    old.bind(base_ms, mono[0])
    for beat, mono_ms in zip(
        [Beat(10, base_ms), Beat(11, base_ms + 200)],
        mono[1:3],
        strict=True,
    ):
        assert old.ingest(beat, mono_ms) is None

    new = ChainModel(token, new_sess, base_ms + 1000, mono[3])
    new.bind(base_ms + 1000, mono[3])
    for beat, mono_ms in zip(
        [Beat(10, base_ms + 1000), Beat(11, base_ms + 1200)],
        [mono[4], mono[4] + 50],
        strict=True,
    ):
        assert new.ingest(beat, mono_ms) is None
    return old, new


def scenario_grace_expired_ban(seed: str) -> ChainModel:
    token = derive_token("player", seed, "late")
    session = derive_session_id("sess-late", seed, "late")
    base_ms = 40000 + (seed_mix(seed, "late:ms") % 400)
    m = ChainModel(token, session, base_ms, 0)
    m.bind(base_ms, 0)
    assert m.ingest(Beat(1, base_ms), 100) is None
    assert m.ingest(Beat(5, base_ms + 7000), 7000) is None
    assert m.ingest(Beat(2, base_ms + 12001), 12001) is None
    assert m.ingest(Beat(3, base_ms + 12100), 12100) is None
    assert m.ingest(Beat(4, base_ms + 12200), 12200) is None
    return m
