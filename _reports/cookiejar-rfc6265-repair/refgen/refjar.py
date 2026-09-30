"""Independent reference cookie jar: RFC 6265 section 5 + crumbjar docs/POLICY.md.

Written straight from the RFC text, not from the Rust sources, to produce the
expected outputs in tests/cases.json.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from pathlib import Path

EARLIEST = -62135596800
LATEST = 253402300799
SITE_LIMIT = 6


def load_psl(path: Path) -> set[str]:
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("//"):
            out.add(line.lower())
    return out


# ---------------------------------------------------------------- 5.1.1 dates

def _delim(ch: int) -> bool:
    return ch == 0x09 or 0x20 <= ch <= 0x2F or 0x3B <= ch <= 0x40 or 0x5B <= ch <= 0x60 or 0x7B <= ch <= 0x7E


_TIME = re.compile(rb"^(\d{1,2}):(\d{1,2}):(\d{1,2})(?:\D.*)?$", re.S)
_DAY = re.compile(rb"^(\d{1,2})(?:\D.*)?$", re.S)
_YEAR = re.compile(rb"^(\d{2,4})(?:\D.*)?$", re.S)
_MONTHS = [b"jan", b"feb", b"mar", b"apr", b"may", b"jun", b"jul", b"aug", b"sep", b"oct", b"nov", b"dec"]


def parse_cookie_date(s: str) -> int | None:
    data = s.encode("utf-8")
    tokens, cur = [], bytearray()
    for b in data:
        if _delim(b):
            if cur:
                tokens.append(bytes(cur))
                cur = bytearray()
        else:
            cur.append(b)
    if cur:
        tokens.append(bytes(cur))

    t = day = mon = year = None
    for tok in tokens:
        if t is None:
            m = _TIME.match(tok)
            if m:
                t = tuple(int(x) for x in m.groups())
                continue
        if day is None:
            m = _DAY.match(tok)
            if m:
                day = int(m.group(1))
                continue
        if mon is None and len(tok) >= 3 and tok[:3].lower() in _MONTHS:
            mon = _MONTHS.index(tok[:3].lower()) + 1
            continue
        if year is None:
            m = _YEAR.match(tok)
            if m:
                year = int(m.group(1))
                continue
    if t is None or day is None or mon is None or year is None:
        return None
    if 70 <= year <= 99:
        year += 1900
    elif 0 <= year <= 69:
        year += 2000
    h, mi, se = t
    if day < 1 or day > 31 or year < 1601 or h > 23 or mi > 59 or se > 59:
        return None
    if day > calendar.monthrange(year, mon)[1]:
        return None
    return calendar.timegm((year, mon, day, h, mi, se, 0, 0, 0))


# ---------------------------------------------------------------- helpers

def is_ip(host: str) -> bool:
    parts = host.split(".")
    if len(parts) != 4:
        return False
    for p in parts:
        if not p or len(p) > 3 or not p.isascii() or not p.isdigit() or int(p) > 255:
            return False
    return True


def domain_match(string: str, domain: str) -> bool:
    if string == domain:
        return True
    return (
        string.endswith(domain)
        and len(string) > len(domain)
        and string[len(string) - len(domain) - 1] == "."
        and not is_ip(string)
    )


def default_path(uri_path: str) -> str:
    if not uri_path.startswith("/"):
        return "/"
    if uri_path.count("/") == 1:
        return "/"
    return uri_path[: uri_path.rindex("/")]


def path_match(req: str, cpath: str) -> bool:
    if req == cpath:
        return True
    if req.startswith(cpath):
        if cpath.endswith("/"):
            return True
        if req[len(cpath)] == "/":
            return True
    return False


@dataclass
class Url:
    raw: str
    secure: bool
    host: str
    path: str


def parse_url(raw: str) -> Url:
    low = raw.lower()
    if low.startswith("https://"):
        secure, rest = True, raw[8:]
    elif low.startswith("http://"):
        secure, rest = False, raw[7:]
    else:
        raise ValueError(raw)
    m = re.match(r"^([^/?#]*)(.*)$", rest, re.S)
    auth, tail = m.group(1), m.group(2)
    if ":" in auth:
        host, port = auth.rsplit(":", 1)
        assert port.isdigit()
    else:
        host = auth
    path = re.split(r"[?#]", tail, maxsplit=1)[0] or "/"
    return Url(raw, secure, host.lower(), path)


# ---------------------------------------------------------------- the jar

@dataclass
class Cookie:
    name: str
    value: str
    domain: str
    path: str
    expiry: int | None
    host_only: bool
    secure: bool
    http_only: bool
    created: tuple[int, int]
    accessed: tuple[int, int]


class Jar:
    def __init__(self, psl: set[str]):
        self.psl = psl
        self.cookies: list[Cookie] = []
        self.now = 0
        self.seq = 0

    def _stamp(self):
        self.seq += 1
        return (self.now, self.seq)

    def site(self, domain: str) -> str:
        if is_ip(domain) or domain in self.psl:
            return domain
        labels = domain.split(".")
        for i in range(1, len(labels)):
            if ".".join(labels[i:]) in self.psl:
                return ".".join(labels[i - 1 :])
        if len(labels) >= 2:
            return ".".join(labels[-2:])
        return domain

    def _purge(self):
        self.cookies = [c for c in self.cookies if not (c.expiry is not None and c.expiry <= self.now)]

    # 5.2 + 5.3
    def set(self, url: Url, header: str):
        ws = " \t"
        if ";" in header:
            nvp, unparsed = header.split(";", 1)
            unparsed = ";" + unparsed
        else:
            nvp, unparsed = header, ""
        if "=" not in nvp:
            return
        name, value = nvp.split("=", 1)
        name, value = name.strip(ws), value.strip(ws)
        if name == "":
            return
        attrs: list[tuple[str, object]] = []
        while unparsed:
            unparsed = unparsed[1:]  # the ';'
            if ";" in unparsed:
                av, unparsed = unparsed.split(";", 1)
                unparsed = ";" + unparsed
            else:
                av, unparsed = unparsed, ""
            if "=" in av:
                an, avv = av.split("=", 1)
            else:
                an, avv = av, ""
            an, avv = an.strip(ws), avv.strip(ws)
            key = an.lower()
            if key == "expires":
                t = parse_cookie_date(avv)
                if t is not None:
                    attrs.append(("expires", min(max(t, EARLIEST), LATEST)))
            elif key == "max-age":
                if not avv or not (avv[0].isdigit() or avv[0] == "-"):
                    continue
                if not all(ch.isdigit() and ch.isascii() for ch in avv[1:]):
                    continue
                if avv == "-":
                    continue
                delta = int(avv)
                if delta <= 0:
                    attrs.append(("max-age", EARLIEST))
                else:
                    attrs.append(("max-age", min(self.now + delta, LATEST)))
            elif key == "domain":
                if avv == "":
                    continue
                d = avv[1:] if avv.startswith(".") else avv
                attrs.append(("domain", d.lower()))
            elif key == "path":
                if avv == "" or not avv.startswith("/"):
                    attrs.append(("path", default_path(url.path)))
                else:
                    attrs.append(("path", avv))
            elif key == "secure":
                attrs.append(("secure", ""))
            elif key == "httponly":
                attrs.append(("httponly", ""))

        def last(k):
            vals = [v for (kk, v) in attrs if kk == k]
            return vals[-1] if vals else None

        stamp = self._stamp()
        if last("max-age") is not None:
            expiry = last("max-age")
        elif last("expires") is not None:
            expiry = last("expires")
        else:
            expiry = None
        domain_attr = last("domain") or ""
        host = url.host
        if domain_attr and domain_attr in self.psl:
            if domain_attr == host:
                domain_attr = ""
            else:
                return
        if domain_attr:
            if not domain_match(host, domain_attr):
                return
            host_only, domain = False, domain_attr
        else:
            host_only, domain = True, host
        p = last("path")
        path = p if p is not None else default_path(url.path)
        secure = last("secure") is not None
        http_only = last("httponly") is not None

        created = stamp
        for i, c in enumerate(self.cookies):
            if c.name == name and c.domain == domain and c.path == path:
                created = c.created
                del self.cookies[i]
                break
        self.cookies.append(Cookie(name, value, domain, path, expiry, host_only, secure, http_only, created, stamp))
        self._purge()
        site = self.site(domain)
        while True:
            members = [c for c in self.cookies if self.site(c.domain) == site]
            if len(members) <= SITE_LIMIT:
                break
            victim = min(members, key=lambda c: (c.accessed, c.created))
            self.cookies.remove(victim)

    # 5.4
    def get(self, url: Url) -> str:
        self._purge()
        stamp = self._stamp()
        hits = []
        for c in self.cookies:
            if c.host_only:
                if url.host != c.domain:
                    continue
            elif not domain_match(url.host, c.domain):
                continue
            if not path_match(url.path, c.path):
                continue
            if c.secure and not url.secure:
                continue
            hits.append(c)
        hits.sort(key=lambda c: (-len(c.path), c.created))
        for c in hits:
            c.accessed = stamp
        return "; ".join(f"{c.name}={c.value}" for c in hits)

    def dump(self) -> list[str]:
        live = [c for c in self.cookies if not (c.expiry is not None and c.expiry <= self.now)]
        live.sort(key=lambda c: (c.domain.encode(), c.path.encode(), c.name.encode()))
        out = [f"-- jar @{self.now}: {len(live)} cookie(s)"]
        for c in live:
            flags = [f for f, on in (("host-only", c.host_only), ("secure", c.secure), ("httponly", c.http_only)) if on]
            out.append(
                "\t".join(
                    [
                        c.domain,
                        c.path,
                        f"{c.name}={c.value}",
                        ",".join(flags) or "-",
                        "session" if c.expiry is None else str(c.expiry),
                        str(c.created[0]),
                        str(c.accessed[0]),
                    ]
                )
            )
        return out


def replay(transcript: str, psl: set[str]) -> str:
    jar = Jar(psl)
    out: list[str] = []
    for raw in transcript.splitlines():
        line = raw.lstrip()
        if not line.strip() or line.startswith("#"):
            continue
        word, _, rest = line.partition(" ")
        if word == "at":
            t = int(rest.strip())
            assert t >= jar.now
            jar.now = t
        elif word == "set":
            u, _, header = rest.partition(" ")
            jar.set(parse_url(u), header)
        elif word == "get":
            u = parse_url(rest.strip())
            out.append(f"{u.raw}\t{jar.get(u)}")
        elif word == "dump":
            out.extend(jar.dump())
        else:
            raise ValueError(line)
    return "".join(x + "\n" for x in out)
