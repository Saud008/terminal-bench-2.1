"""Random transcripts: `gen <dir> <n>` writes them, `check <dir>` compares <i>.out with refjar."""

from __future__ import annotations

import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import refjar  # noqa: E402
from gen_cases import PSL, T0  # noqa: E402

HOSTS = [
    "example.com", "www.example.com", "api.example.com", "a.b.example.com", "example.org",
    "shop.example.co.uk", "co.uk", "x.co.uk", "github.io", "alice.github.io", "10.1.2.3",
    "1.2.3", "192.168.0.1", "localhost", "foo.test",
]
DOMAINS = ["", "example.com", ".example.com", "EXAMPLE.com", "com", "co.uk", "example.co.uk",
           "github.io", "alice.github.io", "1.2.3", "10.1.2.3", "b.example.com", ".", "localhost", "test"]
PATHS = ["/", "/a", "/a/", "/a/b", "/a/b/c", "/ab", "/a/bc/d", "", "/x/y?q=/z", "/a/b/"]
PATH_ATTRS = ["/", "/a", "/a/", "/a/b", "ab", "", "/ab"]
DATES = [
    "Wed, 09 Jun 2021 10:18:14 GMT", "Wed, 09-Jun-61 10:18:14 GMT", "Sun Nov  6 08:49:37 1994",
    "Thu, 01 Jan 2032 00:00:00 GMT", "29 Feb 2100 00:00:00", "29 Feb 2400 00:00:00", "29 Feb 2028 1:2:3",
    "31 Apr 2030 00:00:00", "01-Jan-49 00:00:00", "01-Jan-50 00:00:00", "01-Jan-69 00:00:00",
    "01-Jan-70 00:00:00", "junk", "12:00:00 1 jan 1600", "1 jan 9999 23:59:59", "24:00:00 1 jan 2030",
    "1 January 2031 10:00:00", "2030 12:00:00 5 mar", "05 Mar 2030 12:00:00abc",
]
MAXAGES = ["60", "0", "-5", "+5", "abc", "3600", "999999999999999999999", "-0", "", "20"]
NAMES = ["a", "b", "sid", "z", "A"]


def rand_url(r: random.Random) -> str:
    scheme = r.choice(["http", "https"])
    return f"{scheme}://{r.choice(HOSTS)}{r.choice(PATHS)}"


def rand_header(r: random.Random) -> str:
    roll = r.random()
    if roll < 0.05:
        return r.choice(["noequals", "=v", " ", "\t=x"])
    parts = [f"{r.choice(NAMES)}={r.randint(0, 9)}"]
    for _ in range(r.randint(0, 4)):
        k = r.choice(["domain", "path", "expires", "max-age", "secure", "httponly", "samesite"])
        if k == "domain":
            parts.append(f"Domain={r.choice(DOMAINS)}")
        elif k == "path":
            parts.append(f"Path={r.choice(PATH_ATTRS)}")
        elif k == "expires":
            parts.append(f"Expires={r.choice(DATES)}")
        elif k == "max-age":
            parts.append(f"Max-Age={r.choice(MAXAGES)}")
        elif k == "secure":
            parts.append("Secure")
        elif k == "httponly":
            parts.append("HttpOnly")
        else:
            parts.append("SameSite=Lax")
    return "; ".join(parts)


def gen(dest: Path, n: int) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        r = random.Random(i)
        now = T0
        lines = [f"at {now}"]
        for _ in range(r.randint(5, 40)):
            x = r.random()
            if x < 0.1:
                now += r.choice([0, 1, 30, 100, 4000])
                lines.append(f"at {now}")
            elif x < 0.6:
                lines.append(f"set {rand_url(r)} {rand_header(r)}")
            elif x < 0.95:
                lines.append(f"get {rand_url(r)}")
            else:
                lines.append("dump")
        lines.append("dump")
        (dest / f"{i}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def check(dest: Path) -> int:
    bad = 0
    files = sorted(dest.glob("*.txt"), key=lambda p: int(p.stem))
    for f in files:
        exp = refjar.replay(f.read_text(encoding="utf-8"), PSL)
        got = (dest / f"{f.stem}.out").read_text(encoding="utf-8")
        if exp != got:
            bad += 1
            if bad <= 3:
                print(f"== {f.name} differs")
                for a, b in zip(exp.splitlines(), got.splitlines()):
                    if a != b:
                        print(f"  ref: {a!r}\n  got: {b!r}")
                        break
    print(f"{len(files) - bad}/{len(files)} identical")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen(Path(sys.argv[2]), int(sys.argv[3]))
    else:
        sys.exit(check(Path(sys.argv[2])))
