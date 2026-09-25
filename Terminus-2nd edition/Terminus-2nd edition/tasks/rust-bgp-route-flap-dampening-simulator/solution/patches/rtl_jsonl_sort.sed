s/a\.prefix\.cmp(&b\.prefix)\.then_with(|| a\.peer_id\.cmp(&b\.peer_id))/a.peer_id.cmp(\&b.peer_id).then_with(|| a.prefix.cmp(\&b.prefix))/
