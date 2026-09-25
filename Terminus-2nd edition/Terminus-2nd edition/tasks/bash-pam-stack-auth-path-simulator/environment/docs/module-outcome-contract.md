# Module outcome lookup

modules.json maps module basename to per-subject results. Lookup uses the basename of the module path on each stack line. String results use PAM names: success, ignore, auth_err, cred_insufficient, perm_denied, acct_expired, user_unknown. Missing subject falls back to * entry when present.
