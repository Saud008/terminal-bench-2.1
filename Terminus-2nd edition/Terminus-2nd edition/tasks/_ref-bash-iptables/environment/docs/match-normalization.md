# Match extension normalization

Normalized `match_key` strings are lowercase, comma-free where possible, and built from ordered segments joined by `|`.

## conntrack

iptables `-m conntrack --ctstate RELATED,ESTABLISHED` maps to segment `ct=established,related` (states sorted alphabetically).

iptables `-m conntrack --ctstate NEW` maps to `ct=new`.

## multiport

`--dports 80,22` maps to `dport=22,80` (ports sorted numerically).

## protocol and endpoints

`-p tcp` → `proto=tcp`. `-s 10.0.0.0/8` → `src=10.0.0.0/8`. `-d 192.0.2.0/24` → `dst=192.0.2.0/24`.

## nft side

`tcp dport { 22, 80 }` → `proto=tcp|dport=22,80`.

`ct state established,related` → `ct=established,related`.

## Pairing for export

Rules pair when `chain` maps (INPUT→input, FORWARD→forward, OUTPUT→output) and `match_key` is identical after normalization. Targets must normalize ACCEPT/DROP case-insensitively.

When iptables uses `-m recent` or `-m limit`, do not emit an nft tuple; record unsupported feature instead.
