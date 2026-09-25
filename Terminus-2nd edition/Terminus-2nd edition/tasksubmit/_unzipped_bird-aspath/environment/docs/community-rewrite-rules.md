# Community rewrite rules

On accept, apply peer.community_rewrite. Walk map keys lexicographically ascending. Replace exact community string matches. Never rewrite communities whose ASN part is 0 or 65535.
