package store

const SchemaSQL = `
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT NOT NULL,
    session_id TEXT NOT NULL,
    last_seq INTEGER NOT NULL DEFAULT 0,
    has_last_seq INTEGER NOT NULL DEFAULT 0,
    anchor_client_ms INTEGER NOT NULL DEFAULT 0,
    anchor_mono_ms INTEGER NOT NULL DEFAULT 0,
    admission_ticket TEXT NOT NULL DEFAULT '',
    skew_rejections INTEGER NOT NULL DEFAULT 0,
    duplicate_rejections INTEGER NOT NULL DEFAULT 0,
    ticket_rejections INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (token, session_id)
);

CREATE TABLE IF NOT EXISTS breach_seals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL,
    session_id TEXT NOT NULL,
    from_seq INTEGER NOT NULL,
    to_seq INTEGER NOT NULL,
    missing_span INTEGER NOT NULL,
    opened_mono_ms INTEGER NOT NULL,
    closed INTEGER NOT NULL DEFAULT 0,
    closed_mono_ms INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS breach_repaired (
    breach_id INTEGER NOT NULL,
    seq INTEGER NOT NULL,
    PRIMARY KEY (breach_id, seq)
);

CREATE TABLE IF NOT EXISTS ban_seals (
    breach_id INTEGER PRIMARY KEY,
    token TEXT NOT NULL,
    session_id TEXT NOT NULL,
    issued_mono_ms INTEGER NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS accepted_seqs (
    token TEXT NOT NULL,
    session_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    PRIMARY KEY (token, session_id, seq)
);

CREATE TABLE IF NOT EXISTS counters (
    token TEXT NOT NULL,
    session_id TEXT NOT NULL,
    breaches_opened INTEGER NOT NULL DEFAULT 0,
    breaches_closed INTEGER NOT NULL DEFAULT 0,
    missing_span_total INTEGER NOT NULL DEFAULT 0,
    repair_events INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (token, session_id)
);
`
