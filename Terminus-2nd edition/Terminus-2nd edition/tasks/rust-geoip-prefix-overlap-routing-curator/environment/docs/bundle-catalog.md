# Bundle catalog

compile-feeds admits prefix bundles from `/app/fixtures/bundles/` by default (`NAME.json` for `--bundle NAME`). When the `TB3_FIXTURE_DIR` environment variable is set, admit bundles from `$TB3_FIXTURE_DIR/bundles/` instead (same `NAME.json` layout). When unset, keep the default `/app/fixtures/bundles/` root.

dual-feed-basic exercises nested overlap and identical prefixes across feeds.
reserved-mixed includes loopback and RFC1918 space plus one public prefix.
nested-dup-key stacks /24, /25, and /26 under 203.0.113.0/24 and repeats 203.0.113.192/26 on two feeds for duplicate-key feed_id winner tiebreak.
asn-conflict-lineage repeats 192.0.2.0/24 with different ASNs.
contain-overlap pairs /12 and /24 under 172.16.0.0/12.
