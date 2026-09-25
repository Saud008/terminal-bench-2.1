package pwcore

import "sort"

func PeerWaveOrder(peers []Peer) []string {
	cp := append([]Peer(nil), peers...)
	sort.Slice(cp, func(i, j int) bool {
		if cp[i].WaveRank != cp[j].WaveRank {
			return cp[i].WaveRank < cp[j].WaveRank
		}
		if cp[i].ASN != cp[j].ASN {
			return cp[i].ASN < cp[j].ASN
		}
		return cp[i].PeerID < cp[j].PeerID
	})
	out := make([]string, len(cp))
	for i, p := range cp {
		out[i] = p.PeerID
	}
	return out
}
