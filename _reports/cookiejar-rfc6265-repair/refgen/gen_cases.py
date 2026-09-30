"""Builds tests/cases.json from the transcripts below, with expected output from refjar."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import refjar  # noqa: E402

TASK = HERE.parents[2] / "cookiejar-rfc6265-repair" / "cookiejar-rfc6265-repair"
PSL = refjar.load_psl(TASK / "environment" / "app" / "data" / "public_suffix.dat")

T0 = 1767225600  # 2026-01-01T00:00:00Z

GROUPS: dict[str, list[str]] = {}


def case(group: str, text: str) -> None:
    GROUPS.setdefault(group, []).append(text.strip("\n") + "\n")


# ------------------------------------------------------------ default-path
case("default_path", f"""
at {T0}
set https://docs.example.com/guide/intro/page lang=en
set https://docs.example.com/guide/intro/page theme=dark; Path=guide
set https://docs.example.com/top root=1
set https://docs.example.com/a?next=/x/y/z w=1
set https://docs.example.com/guide/intro/ idx=1
get https://docs.example.com/guide/intro
get https://docs.example.com/guide/intro/
get https://docs.example.com/guide/intropage
get https://docs.example.com/guide
dump
""")
case("default_path", f"""
at {T0}
set http://files.example.net/pub/releases/v2/notes.txt seen=1
set http://files.example.net/pub/releases/v2/notes.txt dl=7; Path=
get http://files.example.net/pub/releases/v2
get http://files.example.net/pub/releases/v2/
get http://files.example.net/pub/releases
get http://files.example.net/pub/releases/v20/x
dump
""")

# ------------------------------------------------------------ path-match
case("path_boundary", f"""
at {T0}
set https://shop.example.com/cart/ c=1; Path=/cart
set https://shop.example.com/ all=1; Path=/
set https://shop.example.com/ api=1; Path=/api/
get https://shop.example.com/cart
get https://shop.example.com/cart/items
get https://shop.example.com/cartography
get https://shop.example.com/api
get https://shop.example.com/api/v2
get https://shop.example.com/apiary
""")
case("path_boundary", f"""
at {T0}
set https://wiki.example.org/ ns=1; Path=/wiki/Talk
set https://wiki.example.org/ ro=1; Path=/w
get https://wiki.example.org/wiki/Talk:Main
get https://wiki.example.org/wiki/Talk/Archive
get https://wiki.example.org/wiki/Talk
get https://wiki.example.org/wiki
get https://wiki.example.org/w/index.php
get https://wiki.example.org/wx
""")

# ------------------------------------------------------------ host-only
case("host_only", f"""
at {T0}
set https://example.com/login sid=abc; Path=/
set https://example.com/ pref=1; Domain=example.com
set https://example.com/ dot=1; Domain=.Example.COM
get https://example.com/
get https://api.example.com/
get https://deep.api.example.com/x
set https://api.example.com/ inner=1
get https://example.com/
get https://api.example.com/
dump
""")
case("host_only", f"""
at {T0}
set https://portal.example.co.uk/ s=1
set https://portal.example.co.uk/ t=1; Domain=
get https://eu.portal.example.co.uk/
get https://portal.example.co.uk/
dump
""")

# ------------------------------------------------------------ IP hosts
case("ip_hosts", f"""
at {T0}
set http://10.1.2.3/ a=1; Domain=1.2.3
set http://10.1.2.3/ b=1; Domain=10.1.2.3
set http://10.1.2.3/ c=1
get http://10.1.2.3/
get http://99.1.2.3/
get http://1.2.3/
dump
""")
case("ip_hosts", f"""
at {T0}
set http://192.168.40.7:8080/admin/ tok=1; Domain=168.40.7; Path=/
set http://192.168.40.7:8080/admin/ keep=1; Path=/
set https://www.123.example.com/ num=1; Domain=123.example.com
get http://192.168.40.7/
get http://10.168.40.7/
get https://x.123.example.com/
dump
""")

# ------------------------------------------------------------ Max-Age vs Expires
case("max_age_precedence", f"""
at {T0}
set https://news.example.org/ a=1; Max-Age=3600; Expires=Wed, 01 Jan 2031 00:00:00 GMT
set https://news.example.org/ b=1; Expires=Wed, 01 Jan 2031 00:00:00 GMT; Max-Age=60
set https://news.example.org/ c=1; Max-Age=soon; Expires=Wed, 01 Jan 2031 00:00:00 GMT
set https://news.example.org/ d=1; Expires=Wed, 01 Jan 2031 00:00:00 GMT; Max-Age=0
set https://news.example.org/ e=1; Max-Age=+60
set https://news.example.org/ f=1; Max-Age=-1
set https://news.example.org/ g=1; Max-Age=0; Expires=Wed, 01 Jan 2031 00:00:00 GMT
dump
at {T0 + 100}
get https://news.example.org/
at {T0 + 3700}
get https://news.example.org/
dump
""")
case("max_age_precedence", f"""
at {T0}
set https://id.example.net/ remember=1; Expires=Fri, 01 Jan 2027 00:00:00 GMT
set https://id.example.net/ remember=2; Max-Age=120; Expires=Sat, 01 Jan 2028 00:00:00 GMT; Max-Age=30
get https://id.example.net/
at {T0 + 60}
get https://id.example.net/
dump
""")

# ------------------------------------------------------------ two-digit years
case("two_digit_years", f"""
at {T0}
set https://app.example.net/ y61=1; Expires=Wed, 09-Jun-61 10:18:14 GMT
set https://app.example.net/ y55=1; Expires=Tue, 01-Jan-55 00:00:00 GMT
set https://app.example.net/ y99=1; Expires=Fri, 31-Dec-99 23:59:59 GMT
set https://app.example.net/ y70=1; Expires=Thu, 01-Jan-70 00:00:01 GMT
set https://app.example.net/ y37=1; Expires=Thu, 01-Jan-37 00:00:00 GMT
set https://app.example.net/ y4d=1; Expires=Mon, 01 Jan 2052 00:00:00 GMT
get https://app.example.net/
dump
""")
case("two_digit_years", f"""
at {T0}
set https://cdn.example.org/ keep=1
set https://cdn.example.org/ keep=2; Expires=Sun, 06-Nov-94 08:49:37 GMT
set https://cdn.example.org/ late=1; expires=06 nov 68 08:49:37
get https://cdn.example.org/
dump
""")

# ------------------------------------------------------------ calendar validity
case("invalid_dates", f"""
at {T0}
set https://pay.example.com/ a=1; Expires=Mon, 29 Feb 2100 12:00:00 GMT
set https://pay.example.com/ b=1; Expires=Tue, 29 Feb 2400 12:00:00 GMT
set https://pay.example.com/ c=1; Expires=Tue, 29 Feb 2028 12:00:00 GMT
set https://pay.example.com/ d=1; Expires=Fri, 31 Apr 2027 00:00:00 GMT
set https://pay.example.com/ f=1; Expires=Sun, 29 Feb 2032 25:00:00 GMT
dump
""")
case("invalid_dates", f"""
at {T0}
set https://pay.example.com/ e=1
set https://pay.example.com/ e=2; Expires=Tue, 29 Feb 2000 00:00:00 GMT
set https://pay.example.com/ h=1; Expires=2200-02-29 00:00:00 feb
get https://pay.example.com/
dump
""")

# ------------------------------------------------------------ replacement
case("replacement", f"""
at {T0}
set https://mail.example.com/ z=1
at {T0 + 60}
set https://mail.example.com/ b=1
at {T0 + 120}
set https://mail.example.com/ z=2
get https://mail.example.com/
set https://mail.example.com/ z=3; Path=/inbox
get https://mail.example.com/inbox
dump
""")
case("replacement", f"""
at {T0}
set https://mail.example.com/ s=1
at {T0 + 5}
set https://mail.example.com/ r=1
at {T0 + 10}
set https://mail.example.com/ s=2; Domain=mail.example.com
get https://x.mail.example.com/
get https://mail.example.com/
dump
""")

# ------------------------------------------------------------ header order
case("header_order", f"""
at {T0}
set https://www.example.com/a/b/c m=1; Path=/a
set https://www.example.com/ z=1; Path=/a/b
set https://www.example.com/ k=1; Path=/
set https://www.example.com/ b=1; Path=/a
set https://www.example.com/ a=1; Domain=example.com; Path=/
set https://www.example.com/ y=1; Path=/a/b
get https://www.example.com/a/b/c
get https://www.example.com/a
""")
case("header_order", f"""
at {T0}
set https://beta.example.io/ zeta=1
set https://beta.example.io/ alpha=1; Domain=example.io
set https://beta.example.io/ mid=1
get https://beta.example.io/
""")

# ------------------------------------------------------------ public suffixes
case("public_suffix", f"""
at {T0}
set https://github.io/ gh=1; Domain=github.io
set https://alice.github.io/ steal=1; Domain=github.io
set https://alice.github.io/ own=1; Domain=alice.github.io
get https://github.io/
get https://alice.github.io/
get https://bob.github.io/
dump
""")
case("public_suffix", f"""
at {T0}
set https://www.example.co.uk/ wide=1; Domain=co.uk
set https://www.example.co.uk/ site=1; Domain=example.co.uk
set https://co.uk/ odd=1; Domain=CO.UK
get https://www.example.co.uk/
get https://co.uk/
get https://x.co.uk/
dump
""")

# ------------------------------------------------------------ per-site limit
case("site_limit", f"""
at {T0}
set https://api.example.com/ c1=1
at {T0 + 1}
set https://api.example.com/ c2=1
at {T0 + 2}
set https://www.example.com/ c3=1
at {T0 + 3}
set https://www.example.com/ c4=1; Domain=example.com
at {T0 + 4}
set https://example.com/ c5=1
at {T0 + 5}
set https://example.com/ c6=1; Max-Age=12
at {T0 + 6}
set https://example.org/ o1=1
at {T0 + 10}
get https://api.example.com/
at {T0 + 20}
set https://www.example.com/ c7=1
at {T0 + 21}
set https://example.com/ c8=1
at {T0 + 22}
set https://api.example.com/ c2=2
at {T0 + 23}
set https://www.example.com/ c9=1
get https://www.example.com/
get https://api.example.com/
dump
""")
case("site_limit", f"""
at {T0}
set https://a.shop.example.co.uk/ p1=1
set https://b.shop.example.co.uk/ p2=1
set https://shop.example.co.uk/ p3=1
set https://other.co.uk/ q1=1
set https://shop.example.co.uk/ p4=1
set https://shop.example.co.uk/ p5=1
at {T0 + 30}
get https://a.shop.example.co.uk/
get https://shop.example.co.uk/
at {T0 + 40}
set https://b.shop.example.co.uk/ p6=1
set https://b.shop.example.co.uk/ p7=1
set https://c.shop.example.co.uk/ p8=1
dump
""")

# ------------------------------------------------------------ nameless pairs
case("name_value_pair", f"""
at {T0}
set https://cdn.example.com/ token
set https://cdn.example.com/ =abc
set https://cdn.example.com/  ; Path=/
set https://cdn.example.com/ ok=1
set https://cdn.example.com/ spaced = two words ; Path=/
set https://cdn.example.com/ empty=
get https://cdn.example.com/
dump
""")
case("name_value_pair", f"""
at {T0}
set https://login.example.org/ flag; Secure
set https://login.example.org/ sid="a=b"; Secure
set https://login.example.org/ 	=tabbed
get https://login.example.org/
dump
""")


def main() -> None:
    out = {"groups": {}}
    for group, transcripts in GROUPS.items():
        out["groups"][group] = [{"transcript": t, "stdout": refjar.replay(t, PSL)} for t in transcripts]
    dest = TASK / "tests" / "cases.json"
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {dest} ({sum(len(v) for v in GROUPS.values())} transcripts)")


if __name__ == "__main__":
    main()
