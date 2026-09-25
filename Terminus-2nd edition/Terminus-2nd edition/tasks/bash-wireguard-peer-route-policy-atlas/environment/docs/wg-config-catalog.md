# WireGuard config catalog

        Each site bundle contains manifest.json listing interface names, site-policy.json, wg/<iface>.conf files, and routes/<iface>-routes.json.

        Bundled sites include coastal-mesh, dual-uplink, and table-split under /app/sites/. Example bundle root: /app/sites/coastal-mesh. coastal-mesh demonstrates peer-alpha endpoint 203.0.113.10:51820 precedence, peer-alpha to peer-delta allowed-IP overlap, and disabled peer-gamma. dual-uplink spoke-one uses endpoint 192.0.2.50:51820 when metric 5 wins. table-split uses cross_interface_table_id route conflicts on table_id 300.

        wgpatlas ingest writes /app/work/{run-id}-ingest.json before analyze runs. Pytest contract helpers use hashlib and ipaddress via /app/scripts/wgpa_cidr_digest_helpers.py.

        Peer stanzas include PublicKey, AllowedIPs as comma-separated CIDR list, optional Endpoint, optional Name for policy lookup.
