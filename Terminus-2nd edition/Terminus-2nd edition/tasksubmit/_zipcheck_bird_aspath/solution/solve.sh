#!/usr/bin/env bash
set -euo pipefail
cd /solution

cat > /app/pwcore/pathmatch.go <<'EOF_PATHMATCH'
package pwcore

func ASPathMatches(f Filter, asPath []int) bool {
	switch f.MatchMode {
	case "origin":
		return len(asPath) > 0 && asPath[len(asPath)-1] == f.ASN
	case "transit":
		if len(asPath) < 2 {
			return false
		}
		for _, a := range asPath[:len(asPath)-1] {
			if a == f.ASN {
				return true
			}
		}
		return false
	case "exact":
		if len(asPath) != len(f.ASPath) {
			return false
		}
		for i := range asPath {
			if asPath[i] != f.ASPath[i] {
				return false
			}
		}
		return true
	default:
		return false
	}
}
EOF_PATHMATCH

cat > /app/pwcore/engine.go <<'EOF_ENGINE'
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
EOF_ENGINE

cat > /app/pwcore/filters.go <<'EOF_FILTERS'
package pwcore

import "sort"

func InheritFilters(inv Inventory, peer Peer) []Filter {
	effective := map[string]Filter{}
	for _, g := range inv.PeerGroups {
		if g.GroupID == peer.GroupID {
			for _, f := range g.Filters {
				effective[f.FilterID] = f
			}
			break
		}
	}
	for _, f := range peer.Filters {
		effective[f.FilterID] = f
	}
	out := make([]Filter, 0, len(effective))
	for _, f := range effective {
		out = append(out, f)
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Priority != out[j].Priority {
			return out[i].Priority > out[j].Priority
		}
		return out[i].FilterID < out[j].FilterID
	})
	return out
}
EOF_FILTERS

cat > /app/pwcore/metric.go <<'EOF_METRIC'
package pwcore

func ClampMed(med int, ceiling *int) int {
	if ceiling == nil {
		return med
	}
	if med < *ceiling {
		return med
	}
	return *ceiling
}
EOF_METRIC

cat > /app/pwcore/comms.go <<'EOF_COMMS'
package pwcore

import "sort"

func IsWellKnown(c string) bool {
	asn := 0
	n := 0
	for i := 0; i < len(c); i++ {
		if c[i] == ':' {
			break
		}
		if c[i] < '0' || c[i] > '9' {
			return false
		}
		asn = asn*10 + int(c[i]-'0')
		n++
	}
	if n == 0 {
		return false
	}
	return asn == 0 || asn == 65535
}

func RewriteCommunities(comms []string, m map[string]string) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	out := append([]string{}, comms...)
	for _, k := range keys {
		to := m[k]
		for i, c := range out {
			if !IsWellKnown(c) && c == k {
				out[i] = to
			}
		}
	}
	return out
}
EOF_COMMS

cat > /app/pwcore/salt.go <<'EOF_SALT'
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
EOF_SALT

cat > /app/pwcore/reportio.go <<'EOF_REPORTIO'
package pwcore

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"
)

func SealReport(led Ledger) Report {
	lines := make([]string, 0, len(led.Rows))
	for _, r := range led.Rows {
		parts := make([]string, len(r.ASPath))
		for i, a := range r.ASPath {
			parts[i] = fmt.Sprintf("%d", a)
		}
		lines = append(lines, fmt.Sprintf("%s|%s|%s|%s", r.PeerID, r.Prefix, r.Action, strings.Join(parts, ",")))
	}
	sum := sha256.Sum256([]byte(strings.Join(lines, "\n")))
	return Report{
		SchemaVersion: 1, RunID: led.RunID, WaveAborted: led.WaveAborted,
		PeerOrder: append([]string{}, led.PeerOrder...), Rows: led.Rows,
		AuditDigest: hex.EncodeToString(sum[:]),
	}
}
EOF_REPORTIO

cat > /app/pwcore/rank.go <<'EOF_RANK'
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
EOF_RANK

bash /app/scripts/rebuild-bgpcut.sh
/usr/local/bin/bgpcut cutover --scenario basic-wave --run-id oracle-smoke --output /app/output/bgp_cutover_report.json
test -s /app/state/cutover-ledger.json
test -s /app/output/bgp_cutover_report.json
