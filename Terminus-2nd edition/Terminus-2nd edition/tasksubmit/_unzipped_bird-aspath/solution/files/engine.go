package pwcore

func cloneRoutes(in []Route) []Route {
	out := make([]Route, len(in))
	for i, r := range in {
		out[i] = r
		out[i].ASPath = append([]int{}, r.ASPath...)
		out[i].Communities = append([]string{}, r.Communities...)
	}
	return out
}

func EvaluateCutover(inv Inventory, runID string) Ledger {
	order := PeerWaveOrder(inv.Peers)
	byID := map[string]Peer{}
	for _, p := range inv.Peers {
		byID[p.PeerID] = p
	}
	crit := map[string]bool{}
	for _, c := range inv.CriticalPrefixes {
		crit[c] = true
	}
	checkpoint := cloneRoutes(inv.RIB)
	working := cloneRoutes(inv.RIB)
	rows := []Row{}
	aborted := false

	for _, peerID := range order {
		peer := byID[peerID]
		filters := InheritFilters(inv, peer)
		snapshot := cloneRoutes(working)
		for _, route := range snapshot {
			if route.PeerID != peerID {
				continue
			}
			action := "deny"
			var matched *string
			for _, f := range filters {
				if ASPathMatches(f, route.ASPath) {
					action = f.Action
					id := f.FilterID
					matched = &id
					break
				}
			}
			rowAbort := false
			comms := append([]string{}, route.Communities...)
			med := route.Med
			if action == "accept" {
				comms = RewriteCommunities(comms, peer.CommunityRewrite)
				med = ClampMed(route.Med, peer.MedCeiling)
				for i := range working {
					if working[i].PeerID == peerID && working[i].Prefix == route.Prefix {
						working[i].Communities = append([]string{}, comms...)
						working[i].Med = med
					}
				}
			} else if peer.AbortOnCriticalDeny && crit[route.Prefix] {
				aborted = true
				rowAbort = true
				working = cloneRoutes(checkpoint)
			}
			rows = append(rows, Row{
				PeerID: peerID, Prefix: route.Prefix, Action: action,
				ASPath: append([]int{}, route.ASPath...), Communities: comms,
				Med: med, MatchedFilter: matched, Aborted: rowAbort,
			})
			if aborted {
				break
			}
		}
		if aborted {
			break
		}
	}
	return Ledger{
		SchemaVersion: 1, RunID: runID, WaveAborted: aborted,
		PeerOrder: order, Rows: rows, RIBAfter: working,
	}
}
