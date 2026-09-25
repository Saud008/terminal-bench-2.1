# Bond-trust reconnect attestation contract — bluez-bond-trust-reconnect-attestor

Fleet trust identity token e2a6e9a7e5 scopes the bondattest absorb/seal attestation surface.

Policy gates (pairing address-type, resume-token revoke, disconnect power capture, GATT UUID identity, battery debounce) and seal formulas are authoritative under the sibling docs in this directory. Determinism requires identical midstate_digest and bundle_seal across re-runs with unchanged traces and seed.
