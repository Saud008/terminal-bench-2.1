"""G-026 smoke entry for kongadmit gateway admission plane."""

from __future__ import annotations

from pathlib import Path

from http_helpers import admin_get, rebuild, start_daemon, stop_daemon
from reference_chain import merge_plugins

CLI = Path("/usr/local/bin/kongadmit")


class TestKongadmitSmoke:
    def setup_method(self) -> None:
        stop_daemon()
        rebuild()
        start_daemon()

    def teardown_method(self) -> None:
        stop_daemon()

    def test_binary_installed(self) -> None:
        """kongadmit must be installed at /usr/local/bin/kongadmit."""
        assert CLI.is_file()

    def test_admin_health(self) -> None:
        """Admin /health must return 200."""
        status, _ = admin_get("/health")
        assert status == 200

    def test_reference_merge_additive_transformer(self) -> None:
        """Reference merge keeps service-only transformer headers when route overlays."""
        svc = [{"name": "response-transformer", "config": {"add": {"headers": ["X-Service:1"]}}}]
        rt = [{"name": "response-transformer", "config": {"add": {"headers": ["X-Route:2"]}}}]
        merged = merge_plugins(svc, rt)
        rt_pl = next(p for p in merged if p["name"] == "response-transformer")
        header_keys = {line.split(":", 1)[0] for line in rt_pl["config"]["add"]["headers"]}
        assert "X-Service" in header_keys
        assert "X-Route" in header_keys
