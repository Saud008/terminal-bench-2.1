CREATE TABLE IF NOT EXISTS packet (
    interface_id INTEGER NOT NULL,
    ts_ns INTEGER NOT NULL,
    file_offset INTEGER NOT NULL,
    cap_len INTEGER NOT NULL,
    packet_len INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS replay_keys (
    replay_key TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS iface_meta (
    interface_id INTEGER PRIMARY KEY,
    if_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingest_stats (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    crc_rejected INTEGER NOT NULL DEFAULT 0,
    duplicate_rejected INTEGER NOT NULL DEFAULT 0,
    accepted INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO ingest_stats (id, crc_rejected, duplicate_rejected, accepted)
VALUES (1, 0, 0, 0);
