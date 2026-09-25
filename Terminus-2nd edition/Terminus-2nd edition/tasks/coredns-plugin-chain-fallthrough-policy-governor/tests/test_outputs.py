"""Behavioral verifier for dnsplugd CoreDNS-style plugin chain."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import pytest

APP = Path("/app")
TEMPLATES = APP / "fixtures" / "templates"
INTEGRITY_MANIFEST = APP / "fixtures" / "template-integrity.json"
CLI = "/usr/local/bin/dnsplugd"
SEED = os.environ.get("VERIFIER_SEED", "coredns-chain-seed-42")

TEMPLATE_SHA256: dict[str, str] = json.loads(
    INTEGRITY_MANIFEST.read_text(encoding="utf-8")
)["sha256"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_template_integrity() -> None:
    """Reject agents that edit immutable fixture templates under /app/fixtures/templates/."""
    for name, expected in TEMPLATE_SHA256.items():
        path = TEMPLATES / name
        assert path.is_file(), f"missing template {name}"
        got = sha256_file(path)
        assert got == expected, f"template {name} was modified (hash {got} != {expected})"


def token() -> str:
    return hashlib.sha256(SEED.encode()).hexdigest()[:10]


def port_for(label: str) -> int:
    h = int(hashlib.sha256(f"{SEED}:{label}".encode()).hexdigest()[:4], 16)
    return 13000 + (h % 1500)


def render(name: str, tok: str) -> tuple[Path, Path | None]:
    core_src = TEMPLATES / f"{name}.core"
    hosts_src = TEMPLATES / f"{name}.hosts"
    core_dst = Path("/tmp") / f"{tok}-{name}.core"
    core_dst.write_text(core_src.read_text(encoding="utf-8").replace("__TOKEN__", tok), encoding="utf-8")
    hosts_dst = None
    if hosts_src.is_file():
        hosts_dst = Path("/tmp") / f"{tok}-{name}.hosts"
        hosts_dst.write_text(hosts_src.read_text(encoding="utf-8").replace("__TOKEN__", tok), encoding="utf-8")
    return core_dst, hosts_dst


def render_bundle(name: str, tok: str) -> tuple[Path, Path | None, dict[str, str]]:
    core_dst, hosts_dst = render(name, tok)
    hosts_src = TEMPLATES / f"{name}.hosts"
    hosts_map = reference_parse_hosts(hosts_dst) if hosts_dst else {}
    if not hosts_map and hosts_src.is_file():
        hosts_map = reference_parse_hosts(hosts_src)
    return core_dst, hosts_dst, hosts_map


def assert_reference_matches(
    core_text: str,
    hosts: dict[str, str],
    qname: str,
    qtype: str,
    status: str,
    answers: list[str],
    *,
    session: ReferenceSession | None = None,
    client_ip: str = "127.0.0.1",
) -> None:
    block = reference_parse_corefile(core_text)
    sess = session or ReferenceSession()
    ref_status, ref_answers = sess.resolve(block, hosts, qname, qtype, client_ip=client_ip)
    assert ref_status == status, f"reference status {ref_status!r} != dig {status!r}"
    if qtype == "A":
        for ip in ref_answers:
            assert any(ip in a for a in answers), f"reference ip {ip} missing from {answers!r}"
    elif qtype == "TXT" and ref_answers:
        assert any(ref_answers[0] in a for a in answers), f"reference txt {ref_answers!r} missing from {answers!r}"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    out_dir = APP / "output"
    if out_dir.is_dir():
        for child in out_dir.iterdir():
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)
    out_dir.mkdir(parents=True, exist_ok=True)


def dig_query(port: int, qname: str, qtype: str = "A") -> tuple[str, list[str]]:
    proc = run(
        [
            "dig",
            "@127.0.0.1",
            "-p",
            str(port),
            qname,
            qtype,
            "+norecurse",
            "+nocmd",
            "+comments",
            "+noedns",
            "+nostats",
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    status = "UNKNOWN"
    for line in proc.stdout.splitlines():
        if "status:" in line:
            status = line.split("status:", 1)[1].strip().split(",")[0].strip()
    answers = [ln for ln in proc.stdout.splitlines() if ln and not ln.startswith(";")]
    return status, answers


class DnsServer:
    def __init__(self, corefile: Path, port: int) -> None:
        self.corefile = corefile
        self.port = port
        self.proc: subprocess.Popen[str] | None = None

    def start(self) -> None:
        self.proc = subprocess.Popen(
            [CLI, "serve", "--corefile", str(self.corefile), "--listen", f"127.0.0.1:{self.port}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        time.sleep(0.4)
        assert self.proc.poll() is None, "dnsplugd exited early"

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()


@pytest.fixture(scope="session", autouse=True)
def _rebuild_dnsplugd() -> None:
    proc = subprocess.run(
        ["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/dnsplugd"],
        cwd=str(APP),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    verify_template_integrity()
    reset()


def test_fixture_templates_integrity() -> None:
    """Bundled Corefile and hosts templates must remain unchanged."""
    verify_template_integrity()


def test_apex_fallthrough_resolves_via_hosts() -> None:
    """Apex queries must fall through rewrite+continue to hosts."""
    tok = token()
    core, _hosts_path, hosts_map = render_bundle("apex-fallthrough", tok)
    core_text = core.read_text(encoding="utf-8")
    port = port_for("apex")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"{tok}.example.test"
        status, answers = dig_query(port, q, "A")
        assert status == "NOERROR"
        assert any("127.0.0.9" in a for a in answers)
        assert_reference_matches(core_text, hosts_map, q, "A", status, answers)
    finally:
        srv.stop()


def test_rewrite_runs_before_hosts() -> None:
    """Suffix rewrite must execute before hosts lookup."""
    tok = token()
    core, _ = render("rewrite-order", tok)
    port = port_for("rewrite")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"app.corp.{tok}.example.test"
        status, answers = dig_query(port, q, "A")
        assert status == "NOERROR"
        assert any("127.0.0.10" in a for a in answers)
    finally:
        srv.stop()


def test_rewrite_stops_without_continue() -> None:
    """Rewrite without continue must terminate before hosts for original or rewritten names."""
    tok = token()
    core, _ = render("rewrite-stop", tok)
    port = port_for("rewrite-stop")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"probe.stop.{tok}.example.test"
        status, answers = dig_query(port, q, "A")
        assert not any("127.0.0.12" in a or "127.0.0.13" in a for a in answers), (
            f"hosts must not answer after terminating rewrite; status={status!r} answers={answers!r}"
        )
    finally:
        srv.stop()


def test_whoami_bad_qname_servfail() -> None:
    """Whoami must surface SERVFAIL for rejected qnames."""
    tok = token()
    core, _ = render("whoami-error", tok)
    port = port_for("whoami")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"probe.bad.whoami.{tok}.example.test"
        status, _answers = dig_query(port, q, "TXT")
        assert status == "SERVFAIL"
    finally:
        srv.stop()


def test_whoami_invalid_client_servfail() -> None:
    """Whoami must surface SERVFAIL when client metadata is unavailable."""
    tok = token()
    core, _ = render("whoami-error", tok)
    port = port_for("whoami-noclient")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"probe.noclient.whoami.{tok}.example.test"
        status, answers = dig_query(port, q, "TXT")
        assert status == "SERVFAIL", f"expected SERVFAIL for unavailable client metadata; got {status!r} answers={answers!r}"
        assert not any("client=" in a for a in answers)
    finally:
        srv.stop()


def test_whoami_ok_txt() -> None:
    """Whoami returns TXT with loopback client address for normal qnames."""
    tok = token()
    core, _ = render("whoami-error", tok)
    port = port_for("whoami-ok")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"probe.whoami.{tok}.example.test"
        status, answers = dig_query(port, q, "TXT")
        assert status == "NOERROR"
        assert any("client=127.0.0.1" in a for a in answers), f"expected loopback client in {answers!r}"
    finally:
        srv.stop()


def test_cache_preserves_nxdomain() -> None:
    """After warming cache, hits must not upgrade stored NXDOMAIN to empty NOERROR."""
    tok = token()
    core, _hosts_path, hosts_map = render_bundle("cache-rcode", tok)
    core_text = core.read_text(encoding="utf-8")
    port = port_for("cache")
    srv = DnsServer(core, port)
    ref_sess = ReferenceSession()
    srv.start()
    try:
        q = f"missing.cache.{tok}.example.test"
        first_status, _first_answers = dig_query(port, q, "A")
        second_status, second_answers = dig_query(port, q, "A")
        assert first_status == "NXDOMAIN"
        assert second_status == "NXDOMAIN", (
            f"cache hit must preserve NXDOMAIN; got {second_status!r} answers={second_answers!r}"
        )
        assert_reference_matches(core_text, hosts_map, q, "A", first_status, _first_answers, session=ref_sess)
        assert_reference_matches(core_text, hosts_map, q, "A", second_status, second_answers, session=ref_sess)
    finally:
        srv.stop()


def test_cache_preserves_servfail() -> None:
    """Cache hits must preserve SERVFAIL from upstream whoami failures."""
    tok = token()
    core, _ = render("whoami-error", tok)
    port = port_for("cache-servfail")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"probe.bad.whoami.{tok}.example.test"
        first_status, _first = dig_query(port, q, "TXT")
        second_status, second_answers = dig_query(port, q, "TXT")
        assert first_status == "SERVFAIL"
        assert second_status == "SERVFAIL", (
            f"cache hit must preserve SERVFAIL; got {second_status!r} answers={second_answers!r}"
        )
    finally:
        srv.stop()


def test_cache_known_host() -> None:
    """Known hosts entries resolve before cache masking matters."""
    tok = token()
    core, _ = render("cache-rcode", tok)
    port = port_for("cache-known")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"known.cache.{tok}.example.test"
        status, answers = dig_query(port, q, "A")
        assert status == "NOERROR"
        assert any("127.0.0.11" in a for a in answers)
    finally:
        srv.stop()


def test_procedural_token_variants() -> None:
    """Different seeds change labels and still resolve apex fallthrough."""
    alt = hashlib.sha256(b"alt-" + SEED.encode()).hexdigest()[:10]
    core = Path("/tmp") / f"{alt}-proc.core"
    core.write_text(
        (TEMPLATES / "apex-fallthrough.core")
        .read_text(encoding="utf-8")
        .replace("__TOKEN__", alt),
        encoding="utf-8",
    )
    hosts = Path("/tmp") / f"{alt}-apex-fallthrough.hosts"
    hosts.write_text(
        (TEMPLATES / "apex-fallthrough.hosts").read_text(encoding="utf-8").replace("__TOKEN__", alt),
        encoding="utf-8",
    )
    port = port_for("proc")
    srv = DnsServer(core, port)
    srv.start()
    try:
        status, answers = dig_query(port, f"{alt}.example.test", "A")
        assert status == "NOERROR"
        assert any("127.0.0.9" in a for a in answers)
    finally:
        srv.stop()


def test_rewrite_cache_hit_after_continue() -> None:
    """Cache must key on post-rewrite names so a second identical query hits."""
    tok = token()
    core, _ = render("rewrite-cache-key", tok)
    port = port_for("rewrite-cache-hit")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"app.rk.{tok}.example.test"
        first_status, first_answers = dig_query(port, q, "A")
        second_status, second_answers = dig_query(port, q, "A")
        assert first_status == "NOERROR"
        assert any("127.0.0.14" in a for a in first_answers)
        assert second_status == "NOERROR"
        assert any("127.0.0.14" in a for a in second_answers), (
            f"cache miss on repeat query; second={second_answers!r}"
        )
    finally:
        srv.stop()


def test_rewrite_cache_preserves_nxdomain_key() -> None:
    """NXDOMAIN after rewrite must cache under the effective name."""
    tok = token()
    core, _ = render("rewrite-cache-key", tok)
    port = port_for("rewrite-cache-nx")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"ghost.rk.{tok}.example.test"
        first_status, _ = dig_query(port, q, "A")
        second_status, second_answers = dig_query(port, q, "A")
        assert first_status == "NXDOMAIN"
        assert second_status == "NXDOMAIN", (
            f"cached NXDOMAIN lost on repeat; got {second_status!r} answers={second_answers!r}"
        )
    finally:
        srv.stop()


def test_hidden_verifier_apex_fallthrough() -> None:
    """Hidden apex template must fall through rewrite+continue to hosts."""
    hidden_dir = Path(os.environ.get("TB3_FIXTURES_DIR", "/opt/verifier-fixtures/coredns-chain"))
    tok = hashlib.sha256(b"tb3-" + SEED.encode()).hexdigest()[:10]
    core_src = hidden_dir / "hidden-apex.core"
    hosts_src = hidden_dir / "hidden-apex.hosts"
    assert core_src.is_file(), f"missing hidden core template at {core_src}"
    core = Path("/tmp") / f"{tok}-hidden.core"
    hosts = Path("/tmp") / f"{tok}-hidden-apex.hosts"
    core.write_text(core_src.read_text(encoding="utf-8").replace("__TOKEN__", tok), encoding="utf-8")
    hosts.write_text(hosts_src.read_text(encoding="utf-8").replace("__TOKEN__", tok), encoding="utf-8")
    port = port_for("hidden-apex")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"hidden.{tok}.example.test"
        status, answers = dig_query(port, q, "A")
        assert status == "NOERROR"
        assert any("127.0.0.88" in a for a in answers), f"hidden apex fallthrough failed: {answers!r}"
    finally:
        srv.stop()


def test_staging_corefile_render_snapshot() -> None:
    """Staging snapshot render must block ingest-only or export-only token substitution holes."""
    tok = token()
    core, hosts_dst = render("rewrite-order", tok)
    staging_text = core.read_text(encoding="utf-8")
    assert tok in staging_text
    assert "__TOKEN__" not in staging_text
    assert hosts_dst is not None
    hosts_text = hosts_dst.read_text(encoding="utf-8")
    assert tok in hosts_text
    assert "__TOKEN__" not in hosts_text


def test_reference_rewrite_order_alignment() -> None:
    """Reference math must agree with live rewrite-order answers."""
    tok = token()
    core, _hosts_path, hosts_map = render_bundle("rewrite-order", tok)
    core_text = core.read_text(encoding="utf-8")
    port = port_for("ref-rewrite-order")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"app.corp.{tok}.example.test"
        status, answers = dig_query(port, q, "A")
        assert_reference_matches(core_text, hosts_map, q, "A", status, answers)
    finally:
        srv.stop()


def test_reference_whoami_ok_txt() -> None:
    """Reference whoami success must match TXT answers."""
    tok = token()
    core, _hosts_path, hosts_map = render_bundle("whoami-error", tok)
    core_text = core.read_text(encoding="utf-8")
    port = port_for("ref-whoami-ok")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"probe.whoami.{tok}.example.test"
        status, answers = dig_query(port, q, "TXT")
        assert_reference_matches(core_text, hosts_map, q, "TXT", status, answers)
    finally:
        srv.stop()


def test_reference_rewrite_stop_terminates() -> None:
    """Reference rewrite without continue must block hosts answers."""
    tok = token()
    core, _hosts_path, hosts_map = render_bundle("rewrite-stop", tok)
    core_text = core.read_text(encoding="utf-8")
    port = port_for("ref-rewrite-stop")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"probe.stop.{tok}.example.test"
        status, answers = dig_query(port, q, "A")
        ref_status, ref_answers = reference_resolve_once(core_text, hosts_map, q, "A")
        assert ref_status == status
        assert not ref_answers
        assert not any("127.0.0.12" in a for a in answers)
    finally:
        srv.stop()


def test_hidden_verifier_cache_known_host() -> None:
    """Hidden TB3 cache bundle must resolve known hosts entries."""
    hidden_dir = Path(os.environ.get("TB3_FIXTURES_DIR", "/opt/verifier-fixtures/coredns-chain"))
    tok = hashlib.sha256(b"tb3-cache-" + SEED.encode()).hexdigest()[:10]
    core_src = hidden_dir / "hidden-cache-nx.core"
    hosts_src = hidden_dir / "hidden-cache-nx.hosts"
    assert core_src.is_file(), f"missing hidden core at {core_src}"
    core = Path("/tmp") / f"{tok}-hidden-cache.core"
    hosts = Path("/tmp") / f"{tok}-hidden-cache.hosts"
    core.write_text(core_src.read_text(encoding="utf-8").replace("__TOKEN__", tok), encoding="utf-8")
    hosts.write_text(hosts_src.read_text(encoding="utf-8").replace("__TOKEN__", tok), encoding="utf-8")
    port = port_for("hidden-cache-known")
    srv = DnsServer(core, port)
    srv.start()
    try:
        q = f"known.hidden.cache.{tok}.example.test"
        status, answers = dig_query(port, q, "A")
        assert status == "NOERROR"
        assert any("127.0.0.77" in a for a in answers)
    finally:
        srv.stop()


# Independent plugin-chain expectation math (parity with /app/docs/corefile-format.md).

_RCODE = {0: "NOERROR", 3: "NXDOMAIN", 2: "SERVFAIL"}


@dataclass
class RewriteRule:
    mode: str
    from_label: str
    to_label: str
    continue_chain: bool


@dataclass
class ServerBlock:
    zone: str
    fallthrough: bool
    plugin_names: list[str]
    rewrite: RewriteRule | None = None
    cache_ttl: int = 30
    hosts_path: str = ""


@dataclass
class _CacheEntry:
    rcode: int
    answers: list[str]
    until: float


@dataclass
class QueryCtx:
    qname: str
    qtype: str
    client_ip: str
    handled: bool = False
    stop_chain: bool = False
    rcode: int = 0
    answers: list[str] = field(default_factory=list)


def reference_parse_hosts(path: Path) -> dict[str, str]:
    table: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        ip, name = line.split(None, 1)
        table[name.rstrip(".")] = ip
    return table


def reference_parse_corefile(text: str) -> ServerBlock:
    zone = ""
    fallthrough = False
    plugin_names: list[str] = []
    rewrite: RewriteRule | None = None
    cache_ttl = 30
    hosts_path = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "{" in line:
            zone = line.split("{", 1)[0].strip().rstrip(":")
            if ":" in zone:
                zone = zone.rsplit(":", 1)[0]
            continue
        if line == "}":
            break
        parts = line.split()
        if not parts:
            continue
        head = parts[0]
        if head == "fallthrough":
            fallthrough = True
        elif head == "plugins":
            plugin_names = parts[1:]
        elif head == "rewrite":
            mode = parts[1]
            cont = parts[-1] == "continue"
            body = parts[2:-1] if cont else parts[2:]
            rewrite = RewriteRule(mode, body[0], body[1], cont)
        elif head == "cache":
            if len(parts) > 1:
                cache_ttl = int(parts[1])
        elif head == "hosts":
            hosts_path = parts[1]
    return ServerBlock(zone, fallthrough, plugin_names, rewrite, cache_ttl, hosts_path)


class ReferenceSession:
    """Stateful cache for repeated reference_resolve calls."""

    def __init__(self) -> None:
        self._cache: dict[str, _CacheEntry] = {}

    def resolve(
        self,
        block: ServerBlock,
        hosts: dict[str, str],
        qname: str,
        qtype: str = "A",
        *,
        client_ip: str = "127.0.0.1",
    ) -> tuple[str, list[str]]:
        qname = qname.rstrip(".")
        if ".noclient." in qname.lower():
            client_ip = ""
        ctx = QueryCtx(qname=qname, qtype=qtype.upper(), client_ip=client_ip)
        cache_key = f"{ctx.qname}|{ctx.qtype}"
        hit = self._cache.get(cache_key)
        if hit and time.time() < hit.until:
            return _RCODE[hit.rcode], list(hit.answers)

        for name in block.plugin_names:
            if ctx.stop_chain:
                break
            cont = True
            if name == "rewrite":
                cont = _rewrite(ctx, block.rewrite)
            elif name == "whoami":
                cont = _whoami(ctx)
                if not cont and ctx.handled:
                    break
            elif name == "cache":
                cont = _cache_read(self._cache, ctx, block.cache_ttl)
                if ctx.handled:
                    break
            elif name == "hosts":
                cont = _hosts(ctx, hosts)
                if ctx.handled:
                    break
            if ctx.handled and not cont:
                break
            if not cont and block.fallthrough:
                continue
            if not cont:
                break

        if not ctx.handled:
            ctx.rcode = 3
        status = _RCODE.get(ctx.rcode, "SERVFAIL")
        if "cache" in block.plugin_names and ctx.handled:
            self._cache[cache_key] = _CacheEntry(
                ctx.rcode,
                list(ctx.answers),
                time.time() + block.cache_ttl,
            )
        return status, list(ctx.answers)


def reference_resolve_once(
    core_text: str,
    hosts: dict[str, str],
    qname: str,
    qtype: str = "A",
    *,
    client_ip: str = "127.0.0.1",
) -> tuple[str, list[str]]:
    block = reference_parse_corefile(core_text)
    return ReferenceSession().resolve(block, hosts, qname, qtype, client_ip=client_ip)


def _rewrite(ctx: QueryCtx, rule: RewriteRule | None) -> bool:
    if rule is None:
        return True
    before = ctx.qname
    if rule.mode == "suffix" and ctx.qname.endswith(rule.from_label):
        ctx.qname = ctx.qname[: -len(rule.from_label)] + rule.to_label
    elif rule.mode == "exact" and ctx.qname == rule.from_label:
        ctx.qname = rule.to_label
    if ctx.qname != before:
        ctx.handled = True
        if rule.continue_chain:
            return True
        ctx.stop_chain = True
        return False
    return True


def _whoami(ctx: QueryCtx) -> bool:
    if ctx.qtype != "TXT":
        return True
    if ".bad." in ctx.qname.lower():
        ctx.rcode = 2
        ctx.handled = True
        ctx.stop_chain = True
        return False
    if not ctx.client_ip or not re.match(r"^\d+\.\d+\.\d+\.\d+$", ctx.client_ip):
        ctx.rcode = 2
        ctx.handled = True
        ctx.stop_chain = True
        return False
    ctx.rcode = 0
    ctx.answers = [f"client={ctx.client_ip}"]
    ctx.handled = True
    ctx.stop_chain = True
    return False


def _cache_read(store: dict[str, _CacheEntry], ctx: QueryCtx, ttl: int) -> bool:
    key = f"{ctx.qname}|{ctx.qtype}"
    ent = store.get(key)
    if ent and time.time() < ent.until:
        ctx.rcode = ent.rcode
        ctx.answers = list(ent.answers)
        ctx.handled = True
        ctx.stop_chain = True
        return False
    return True


def _hosts(ctx: QueryCtx, hosts: dict[str, str]) -> bool:
    if ctx.qtype not in {"A", "AAAA"}:
        return True
    ip = hosts.get(ctx.qname)
    if not ip:
        ctx.rcode = 3
        ctx.handled = True
        ctx.stop_chain = True
        return False
    ctx.rcode = 0
    ctx.answers = [ip]
    ctx.handled = True
    ctx.stop_chain = True
    return False
