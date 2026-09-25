CREATE TABLE IF NOT EXISTS shadow_entries (
  normalized_dn TEXT PRIMARY KEY,
  attrs_json TEXT NOT NULL DEFAULT '{}',
  usn_changed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS usn_applied (
  usn_changed INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS export_meta (
  key TEXT PRIMARY KEY,
  value INTEGER NOT NULL
);
