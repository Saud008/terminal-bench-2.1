package store

const SchemaSQL = `
CREATE TABLE IF NOT EXISTS guilds (
    guild_id TEXT PRIMARY KEY,
    gold_balance INTEGER NOT NULL,
    interest_rate_bps INTEGER NOT NULL,
    created_mono_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS item_stacks (
    stack_id TEXT PRIMARY KEY,
    guild_id TEXT NOT NULL,
    item_template_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    bound INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS withdraw_slices (
    slice_id TEXT PRIMARY KEY,
    guild_id TEXT NOT NULL,
    player_id TEXT NOT NULL,
    source_stack_id TEXT NOT NULL,
    item_template_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    created_mono_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS player_stacks (
    stack_id TEXT PRIMARY KEY,
    guild_id TEXT NOT NULL,
    player_id TEXT NOT NULL,
    item_template_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    bound INTEGER NOT NULL DEFAULT 0,
    created_mono_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_entries (
    entry_id TEXT PRIMARY KEY,
    guild_id TEXT NOT NULL,
    op_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    committed INTEGER NOT NULL DEFAULT 0,
    mono_ms INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS interest_journal (
    period_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    interest_amount INTEGER NOT NULL,
    status TEXT NOT NULL,
    started_mono_ms INTEGER NOT NULL,
    finished_mono_ms INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (period_id, guild_id)
);

CREATE TABLE IF NOT EXISTS tx_lock (
    lock_id INTEGER PRIMARY KEY
);
`
