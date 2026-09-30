"""Fixture definitions for zonefile-master-repair (authoring only, not shipped).

Every case: origin, entry file, files, and the error position we expect
(derived by hand from docs, checked against the reference build).
"""

SOA = "@ IN SOA ns1 hostmaster 2026092701 2h 30m 2w 5m"


def case(name, origin, files, entry="main.zone", error=None):
    return {"name": name, "origin": origin, "entry": entry, "files": files, "error": error}


GROUPS = {}

GROUPS["owner_continuation"] = [
    case("origin_between_records", "example.com", {
        "main.zone": f"""$TTL 3600
{SOA}
    IN NS ns1
ns1  IN A 192.0.2.1
mail IN A 192.0.2.25
$ORIGIN lab.example.com.
     IN AAAA 2001:db8::25
     IN MX 10 relay
build IN A 192.0.2.40
$ORIGIN example.com.
     IN TXT "build box"
""",
    }),
    case("relative_origin_and_at", "corp.example", {
        "main.zone": f"""$TTL 1h
{SOA}
  IN NS ns1
ns1 IN A 198.51.100.1
gw  IN A 198.51.100.254
$ORIGIN eu
  IN TXT "gateway for eu"
@ IN NS ns1
$ORIGIN fra
  IN A 198.51.100.100
db IN A 198.51.100.101
$TTL 5m
  IN AAAA 2001:db8:e0::101
""",
    }),
]

GROUPS["default_ttl"] = [
    case("dollar_ttl_beats_record_ttl", "example.org", {
        "main.zone": """@ 86400 IN SOA ns1 hostmaster 1 1h 15m 1w 1h
$TTL 300
      IN NS ns1
ns1   3600 IN A 192.0.2.1
www   IN A 192.0.2.2
api   IN 120 A 192.0.2.3
cdn   IN A 192.0.2.4
""",
    }),
    case("last_record_ttl_then_dollar", "example.org", {
        "main.zone": """@ IN SOA ns1 hostmaster 1 1h 15m 1w 600
      IN NS ns1
ns1   7200 IN A 192.0.2.11
ns2   IN A 192.0.2.12
$TTL 1d
ns3   IN A 192.0.2.13
ns4   60 IN A 192.0.2.14
ns5   IN A 192.0.2.15
""",
    }),
    case("no_ttl_before_soa", "example.org", {
        "main.zone": """www IN A 192.0.2.80
@ IN SOA ns1 hostmaster 1 1h 15m 1w 600
""",
    }, error=("main.zone", 1)),
]

GROUPS["include_scope"] = [
    case("dollar_ttl_inside_include", "example.net", {
        "main.zone": f"""$TTL 1h
{SOA}
    IN NS ns1
$INCLUDE lab.inc lab
ns1 IN A 192.0.2.1
    IN TXT "after include"
www IN A 192.0.2.8
$INCLUDE more.inc
    IN AAAA 2001:db8::8
""",
        "lab.inc": """$TTL 60
@  IN A 192.0.2.100
db IN A 192.0.2.101
""",
        "more.inc": """api 120 IN A 192.0.2.9
    IN TXT "api"
""",
    }),
    case("record_ttl_inside_include", "example.net", {
        "main.zone": """@ 3600 IN SOA ns1 hostmaster 7 1h 15m 1w 300
   IN NS ns1
$INCLUDE hosts.inc
ns1 IN A 192.0.2.1
$ORIGIN svc
mq  IN A 192.0.2.50
""",
        "hosts.inc": """  IN MX 5 mail
mail 30 IN A 192.0.2.30
$ORIGIN internal.example.net.
ldap IN A 10.0.0.5
""",
    }),
]

GROUPS["include_paths"] = [
    case("nested_relative_includes", "example.com", {
        "zones/main.zone": f"""$TTL 1h
{SOA}
$INCLUDE common/ns.inc
www IN A 192.0.2.80
$INCLUDE ../shared/mx.inc
""",
        "zones/common/ns.inc": """@ IN NS ns1
@ IN NS ns2
$INCLUDE glue.inc
""",
        "zones/common/glue.inc": """ns1 IN A 192.0.2.53
ns2 IN A 192.0.2.54
""",
        "shared/mx.inc": """@ IN MX 10 mx1
mx1 IN A 192.0.2.25
""",
    }, entry="zones/main.zone"),
    case("error_in_nested_include", "example.com", {
        "zones/main.zone": f"""$TTL 1h
{SOA}
$INCLUDE common/ns.inc
""",
        "zones/common/ns.inc": """@ IN NS ns1
$INCLUDE glue.inc
""",
        "zones/common/glue.inc": """; glue records
ns1 IN A 192.0.2.53
ns2 IN A 192.0.2.300
""",
    }, entry="zones/main.zone", error=("zones/common/glue.inc", 3)),
]

GROUPS["quoted_parentheses"] = [
    case("parens_and_semicolons_in_strings", "example.com", {
        "main.zone": """$TTL 1h
@ IN SOA ns1 hostmaster (
        2026092701 ; serial
        2h 30m 2w 5m )
  IN NS ns1
ns1   IN A 192.0.2.1
smile IN TXT "ok :-)" "(beta)"
multi IN TXT ( "first; not a comment" ; a real comment
               "second (part" )
caa   IN CAA 0 iodef "mailto:dns@example.com;(24h)"
esc   IN TXT "a \\"quoted\\" word" \\(bare\\)
""",
    }),
    case("unbalanced_parenthesis", "example.com", {
        "main.zone": """$TTL 1h
@ IN SOA ns1 hostmaster 1 2h 30m 2w 5m
  IN NS ns1
ns1 IN A 192.0.2.1
note IN TXT "fine (really)"
bad IN TXT ( "never closed"
""",
    }, error=("main.zone", 6)),
]

GROUPS["escaped_case"] = [
    case("decimal_escapes_fold_case", "example.com", {
        "main.zone": """$TTL 1h
@ IN SOA ns1 hostmaster 1 2h 30m 2w 5m
  IN NS NS1
\\078\\083\\049 IN A 192.0.2.1
\\065pex IN A 192.0.2.10
apex IN A 192.0.2.10
APEX IN A 192.0.2.11
alias IN CNAME \\066ACK\\069nd.Example.COM.
backend IN A 192.0.2.12
host\\.one IN A 192.0.2.13
_srv._tcp IN SRV 0 5 443 \\066ackend
""",
    }),
]

LONG_OK = "\\097" * 20 + "b" * 43           # 63 octets, 123 characters
LONG_OK2 = "\\." * 40 + "c" * 23             # 63 octets, 103 characters
LONG_BAD = "d" * 64                          # 64 octets

GROUPS["escaped_label_length"] = [
    case("sixty_three_octet_labels", "example.com", {
        "main.zone": f"""$TTL 1h
@ IN SOA ns1 hostmaster 1 2h 30m 2w 5m
  IN NS ns1
ns1 IN A 192.0.2.1
{LONG_OK} IN A 192.0.2.63
{LONG_OK2} IN TXT "dots"
link IN CNAME {LONG_OK}
""",
    }),
    case("sixty_four_octet_label", "example.com", {
        "main.zone": f"""$TTL 1h
@ IN SOA ns1 hostmaster 1 2h 30m 2w 5m
  IN NS ns1
ns1 IN A 192.0.2.1
{LONG_OK} IN A 192.0.2.63
{LONG_BAD} IN A 192.0.2.64
""",
    }, error=("main.zone", 6)),
]

GROUPS["canonical_order"] = [
    case("rfc4034_name_order", "example", {
        "main.zone": """$TTL 1h
z.a     IN A 192.0.2.1
yljkjljk.a IN A 192.0.2.2
Z.a     IN TXT "same owner as z.a"
@       IN SOA ns1 hostmaster 1 2h 30m 2w 5m
@       IN NS ns1
a-b     IN A 192.0.2.3
a       IN A 192.0.2.4
*.z.a   IN A 192.0.2.5
\\200.z.a IN A 192.0.2.6
zabc.a  IN A 192.0.2.7
b       IN A 192.0.2.8
ns1     IN A 192.0.2.9
\\001.z.a IN A 192.0.2.10
""",
    }),
    case("type_and_rdata_order", "example.net", {
        "main.zone": """$TTL 1h
@ IN CAA 0 issue "ca.example"
@ IN TXT "aaa"
@ IN TXT "zz"
@ IN AAAA 2001:db8::1
@ IN MX 20 mx
@ IN MX 5 mx
@ IN SOA ns1 hostmaster 1 2h 30m 2w 5m
@ IN NS ns2
@ IN NS ns1
@ IN A 192.0.2.10
@ IN A 192.0.2.9
mx IN A 192.0.2.25
ns1 IN A 192.0.2.53
ns2 IN A 192.0.2.54
""",
    }),
]

GROUPS["rrset_ttl"] = [
    case("first_record_sets_rrset_ttl", "example.com", {
        "main.zone": """$TTL 1h
@ IN SOA ns1 hostmaster 1 2h 30m 2w 5m
  IN NS ns1
  60 IN NS ns2
ns1 IN A 192.0.2.53
ns2 IN A 192.0.2.54
www 600 IN A 192.0.2.1
www 60 IN A 192.0.2.2
www IN AAAA 2001:db8::1
api IN A 192.0.2.3
api 30 IN A 192.0.2.4
api 30 IN A 192.0.2.3
""",
    }),
    case("rrset_split_across_include", "example.com", {
        "main.zone": """$TTL 1h
@ IN SOA ns1 hostmaster 1 2h 30m 2w 5m
  IN NS ns1
ns1 IN A 192.0.2.53
$INCLUDE web.inc
web 90 IN A 192.0.2.81
""",
        "web.inc": """web 7200 IN A 192.0.2.80
web 45 IN TXT "edge"
""",
    }),
]

ZERO48 = "00" * 48
DKIM = "v=DKIM1; k=rsa; p=" + ("MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDwq7ve1Hc9Lr2" * 4)[:139]
assert len(DKIM) == 157

GROUPS["zonemd"] = [
    case("digest_uses_listing_ttls_and_soa_serial", "example.org", {
        "main.zone": f"""$TTL 1h
@ IN SOA ns1 hostmaster 2026092705 2h 30m 2w 5m
  IN NS ns1
  IN ZONEMD 1 1 1 {ZERO48}
ns1 IN A 192.0.2.53
www 600 IN A 192.0.2.80
www 60 IN A 192.0.2.81
""",
    }),
    case("zonemd_below_apex_is_data", "example.org", {
        "main.zone": f"""$TTL 1h
@ IN SOA ns1 hostmaster 2026092704 2h 30m 2w 5m
  IN NS ns1
  IN ZONEMD 2026092704 1 1 ( {ZERO48[:48]}
                             {ZERO48[48:]} )
ns1 IN A 192.0.2.53
archive IN TXT "digest of the retired zone"
archive IN ZONEMD 2025010101 1 1 9F3C0E5A7B21D4C8E6F0A1B2C3D4E5F60718293A4B5C6D7E8F90A1B2C3D4E5F60718293A4B5C6D7E8F90A1B2C3D4E5F6
""",
    }),
    case("digest_input_near_block_end", "example.org", {
        "main.zone": f"""$TTL 1h
@ IN SOA ns1 hostmaster 2026092706 2h 30m 2w 5m
  IN NS ns1
  IN ZONEMD 2026092706 1 1 {ZERO48[:48]} {ZERO48[48:]}
ns1 IN A 192.0.2.53
mail IN A 192.0.2.25
  IN TXT "{DKIM}"
""",
    }),
    case("apex_zonemd_sha512_rejected", "example.org", {
        "main.zone": f"""$TTL 1h
@ IN SOA ns1 hostmaster 2026092707 2h 30m 2w 5m
  IN NS ns1
ns1 IN A 192.0.2.53
@ IN ZONEMD 2026092707 1 2 {ZERO48}{ZERO48[:32]}
""",
    }, error=("main.zone", 5)),
]

GROUPS["reference_zone"] = [
    case("production_like_zone", "shop.example", {
        "db/shop.example.zone": """; shop.example - production
$TTL 4h
@   IN SOA ns1.shop.example. hostmaster.shop.example. (
            2026092703 ; serial
            1h         ; refresh
            15m        ; retry
            2w         ; expire
            10m )      ; minimum
    IN NS   ns1
    IN NS   NS2.Provider.example.
    IN MX   10 mx1
    IN MX   20 mx2
    IN TXT  "v=spf1 mx include:_spf.provider.example ~all"
    IN CAA  0 issue "letsencrypt.org"
    IN CAA  128 iodef "mailto:security@shop.example"
    IN ZONEMD 0 1 1 ( 000000000000000000000000000000000000000000000000
                      000000000000000000000000000000000000000000000000 )
ns1 IN A    203.0.113.53
    IN AAAA 2001:DB8:0:0:1:0:0:53
mx1 IN A    203.0.113.25
mx2 IN A    203.0.113.26
www 300 IN CNAME cdn.provider.example.
$INCLUDE ../fragments/api.inc api
$ORIGIN _tcp.shop.example.
_imaps IN SRV 0 1 993 mx1.shop.example.
_submission IN SRV 0 1 587 mx1.shop.example.
_imaps IN SRV 10 1 993 mx2.shop.example.
$ORIGIN shop.example.
    IN TXT "imaps fallback on mx2"
Status IN A 203.0.113.99
status IN A 203.0.113.99
""",
        "fragments/api.inc": """$TTL 5m
@     IN A    203.0.113.80
      IN A    203.0.113.81
v2    IN CNAME @
docs  IN TXT  ( "api v2 (beta); see"
                "https://shop.example/docs" )
$INCLUDE internal/hosts.inc internal
""",
        "fragments/internal/hosts.inc": """\\068B01 IN A 10.20.0.11
db01  3600 IN TXT "primary"
db02  IN A    10.20.0.12
""",
    }, entry="db/shop.example.zone"),
]
