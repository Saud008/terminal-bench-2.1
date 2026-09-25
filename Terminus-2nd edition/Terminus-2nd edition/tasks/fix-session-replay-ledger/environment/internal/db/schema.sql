CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY,
    session_file TEXT NOT NULL,
    file_offset INTEGER NOT NULL,
    cl_ord_id TEXT NOT NULL,
    exec_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    last_qty REAL NOT NULL DEFAULT 0,
    last_px REAL NOT NULL DEFAULT 0,
    order_qty REAL NOT NULL DEFAULT 0,
    msg_type TEXT NOT NULL,
    exec_type TEXT NOT NULL,
    sending_time TEXT NOT NULL,
    raw_message BLOB NOT NULL
);
