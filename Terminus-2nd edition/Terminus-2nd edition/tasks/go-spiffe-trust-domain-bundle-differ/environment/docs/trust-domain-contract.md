# Trust-domain host folding

Trust domain host labels are lowercased.

The spiffe:// prefix is stripped from trust_domain field values.

SPIFFE IDs in x509_svid retain the spiffe:// prefix. Both the host labels and the path segments after the host are lowercased (for example `spiffe://Example.ORG/Ns/Svc` becomes `spiffe://example.org/ns/svc`).
