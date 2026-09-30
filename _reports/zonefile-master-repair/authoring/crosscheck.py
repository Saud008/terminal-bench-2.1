"""Independent re-derivation of the success listings with dnspython.

Include paths are rewritten to absolute paths first (zonec resolves them
against the including file; dnspython uses the cwd). dnspython gives an
RRset the minimum TTL, zonec the first record's TTL, so for RRsets whose
input TTLs differ the TTL column is compared against a first-record value
computed here from the input order dnspython reports per rdataset... which
it doesn't keep; those lines are listed as TTL-only differences instead.
"""
import json
import re
import shutil
import sys
from pathlib import Path

import dns.name
import dns.rdata
import dns.rdataclass
import dns.rdatatype
import dns.zone

cases = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["groups"]
root = Path("/tmp/xc")
shutil.rmtree(root, ignore_errors=True)
inc = re.compile(r"^\$INCLUDE\s+(\S+)(.*)$", re.M)
bad = 0
for group, lst in cases.items():
    for c in lst:
        if c["rc"] != 0:
            continue
        base = root / group / c["name"]
        for rel, text in c["files"].items():
            p = base / rel
            p.parent.mkdir(parents=True, exist_ok=True)

            def fix(m, d=p.parent):
                return f"$INCLUDE {(d / m.group(1)).as_posix()}{m.group(2)}"

            p.write_text(inc.sub(fix, text), encoding="utf-8")
        origin = dns.name.from_text(c["origin"])
        z = dns.zone.from_file(str(base / c["entry"]), origin=origin, relativize=False,
                               check_origin=False, allow_include=True)
        recs = []
        for name, node in z.nodes.items():
            cname = name.canonicalize()
            for rds in node.rdatasets:
                for rd in rds:
                    wire = rd.to_digestable(origin)
                    crd = dns.rdata.from_wire(dns.rdataclass.IN, rds.rdtype, wire, 0, len(wire))
                    recs.append((cname, rds.rdtype, wire, rds.ttl, crd))
        recs.sort(key=lambda r: (r[0], r[1], r[2]))
        mine = [f"{n.to_text()}\t{t}\tIN\t{dns.rdatatype.to_text(ty)}\t{rd.to_text(relativize=False)}"
                for n, ty, w, t, rd in recs]
        ours = c["stdout"].splitlines()
        if mine != ours:
            strip = lambda ls: [re.sub(r"\t\d+\t", "\t-\t", x, count=1) for x in ls]
            kind = "TTL-only" if strip(mine) == strip(ours) else "CONTENT"
            if kind == "CONTENT":
                bad += 1
            print(f"--- {group}/{c['name']}: {kind} difference")
            for a, b in zip(mine, ours):
                if a != b:
                    print(f"  dnspython: {a}\n  zonec:     {b}")
            if len(mine) != len(ours):
                print(f"  line counts {len(mine)} vs {len(ours)}")
        else:
            print(f"ok  {group}/{c['name']}")

        # ZONEMD: recompute the digest from zonec's own listing with dnspython.
        apex = [l for l in ours if l.split("\t")[3] == "ZONEMD" and l.split("\t")[0] == origin.to_text()]
        if apex:
            lz = dns.zone.from_text("\n".join(ours) + "\n", origin=origin, relativize=False, check_origin=False)
            want = lz.compute_digest(dns.zone.DigestHashAlgorithm.SHA384)
            soa_serial = next(l for l in ours if l.split("\t")[3] == "SOA").split("\t")[4].split()[2]
            f = apex[0].split("\t")[4].split()
            ok = f[0] == soa_serial and f[1] == "1" and f[2] == "1" and f[3] == want.digest.hex().upper()
            print(f"    zonemd {'ok' if ok else 'MISMATCH'}: zonec {f[3][:16]}.. dnspython {want.digest.hex().upper()[:16]}.. serial {f[0]} vs SOA {soa_serial}")
            if not ok:
                bad += 1
sys.exit(1 if bad else 0)
