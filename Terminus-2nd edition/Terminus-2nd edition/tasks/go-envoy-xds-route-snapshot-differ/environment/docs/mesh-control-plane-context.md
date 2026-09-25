# Mesh control-plane snapshot differ context

xsnapctl compares two frozen xDS JSON revisions from the same mesh cell. It is not a live xDS server and does not push configuration to Envoy proxies.

The differ focuses on listener filter chains, virtual host route tables, cluster endpoint weights, and SDS secret name references. Promotion gates require byte-stable diff reports after canonicalization.

Canonicalization must run before diff publication. The normalize_revision counter records that canonicalization completed for the staged pair.
