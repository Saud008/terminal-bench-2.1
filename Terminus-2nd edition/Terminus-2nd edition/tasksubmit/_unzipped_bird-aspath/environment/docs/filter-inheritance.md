# Filter inheritance

Start from peer_group.filters for peer.group_id. Peer-local filters with the same filter_id replace the group entry; new filter_id values are added. Sort by priority descending, then filter_id ascending. First matching filter wins; if none match, action is deny.
