"""Reference contract unit probes for OIDC JWKS governor math."""

from oidc_verdict_refmath import audience_ok, cache_fresh, grace_sec, in_grace, is_revoked, issuer_ok, kid_match


def test_jgov_ref_kid_casefold_match() -> None:
    """Verify reference kid_match is case-insensitive per kid-lookup-contract.md."""
    assert kid_match("Key-Alpha", "key-alpha") is True


def test_jgov_ref_issuer_case_insensitive() -> None:
    """Verify reference issuer_ok ignores case per issuer-audience-contract.md."""
    assert issuer_ok("HTTPS://Auth.Example.NET", "https://auth.example.net") is True


def test_jgov_ref_audience_requires_all_entries() -> None:
    """Verify reference audience_ok requires every token aud in policy per issuer-audience-contract.md."""
    assert audience_ok(["api.example.net", "admin.example.net"], ["api.example.net"]) is False
    assert audience_ok(["api.example.net"], ["api.example.net", "admin.example.net"]) is True


def test_jgov_ref_cache_fresh_seconds() -> None:
    """Verify reference cache_fresh uses seconds per cache-max-age-contract.md."""
    assert cache_fresh(480, 500, 30) is True
    assert cache_fresh(400, 500, 30) is False


def test_jgov_ref_grace_inclusive_bounds() -> None:
    """Verify reference in_grace uses inclusive bounds per grace-window-contract.md."""
    assert in_grace(200, 200, 60) is True
    assert in_grace(260, 200, 60) is True
    assert in_grace(261, 200, 60) is False


def test_jgov_ref_revoked_list_match() -> None:
    """Verify reference is_revoked matches kids case-insensitively per revoked-key-contract.md."""
    assert is_revoked("Live", ["live", "other"]) is True


def test_jgov_ref_grace_sec_env_override() -> None:
    """Verify TB3_GRACE_SEC overrides default grace seconds per grace-window-contract.md."""
    import os

    os.environ["TB3_GRACE_SEC"] = "45"
    try:
        assert grace_sec(120) == 45
    finally:
        del os.environ["TB3_GRACE_SEC"]
