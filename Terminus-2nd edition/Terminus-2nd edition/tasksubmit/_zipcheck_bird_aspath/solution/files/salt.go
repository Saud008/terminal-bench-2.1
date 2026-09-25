package pwcore

func ApplyPeerSalt(inv Inventory, salt string) Inventory {
	out := inv
	peers := make([]Peer, len(inv.Peers))
	for i, p := range inv.Peers {
		peers[i] = p
		peers[i].PeerID = p.PeerID + salt
	}
	rib := make([]Route, len(inv.RIB))
	for i, r := range inv.RIB {
		rib[i] = r
		rib[i].ASPath = append([]int{}, r.ASPath...)
		rib[i].Communities = append([]string{}, r.Communities...)
		rib[i].PeerID = r.PeerID + salt
	}
	out.Peers = peers
	out.RIB = rib
	return out
}
