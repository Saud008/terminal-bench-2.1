# Session expiry contract

CONNECT carries clean_session and session_expiry_ms. Clean session true wipes prior session state for the client. Events with timestamp_ms strictly after connect_ms plus session_expiry_ms are ignored for subscribe and offline delivery processing. TB3_SESSION_EXPIRY_MS may override expiry window in verifier-only scenarios.
