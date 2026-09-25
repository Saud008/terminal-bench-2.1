SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS parties (
 party_id TEXT PRIMARY KEY, leader_id TEXT NOT NULL, status TEXT NOT NULL,
 max_members INTEGER NOT NULL, created_mono_ms INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS members (
 party_id TEXT NOT NULL, player_id TEXT NOT NULL, role TEXT NOT NULL,
 status TEXT NOT NULL, joined_mono_ms INTEGER NOT NULL,
 PRIMARY KEY (party_id, player_id));
CREATE TABLE IF NOT EXISTS invites (
 invite_id TEXT PRIMARY KEY, party_id TEXT NOT NULL, invitee_id TEXT NOT NULL,
 status TEXT NOT NULL, expires_mono_ms INTEGER NOT NULL, created_mono_ms INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS idempotency (
 idempotency_key TEXT PRIMARY KEY, status_code INTEGER NOT NULL,
 body_json TEXT NOT NULL, created_mono_ms INTEGER NOT NULL);
"""
