# Atlas row schema

catalog_rows sorted by holder ascending, then band_id ascending, then site_id ascending.

Each row includes site_id, license_id, holder, band_id, effective_mhz_low, effective_mhz_high, excluded boolean, overlap_peer_count (count of other bundle bands whose MHz ranges overlap including touching endpoints), valid_through, atlas_seq_id.

summary includes total_sites, active_sites (not excluded), excluded_sites, overlap_pairs (unordered pairs of rows on different bands with overlapping MHz ranges), expired_dropped.

audit_digest is SHA-256 hex over stable JSON with keys active_sites, expired_dropped, overlap_pairs, total_sites.
