package party

import "github.com/terminus/party-invite/internal/store"

// LegacyCapGuard is a legacy occupancy helper retained for backward compatibility.
// Audit export and invite cap checks use DAO.EffectiveOccupancy — not this helper.
// See /app/docs/staging-digest.md.
type LegacyCapGuard struct {
	Store *store.Store
}

func NewLegacyCapGuard(st *store.Store) *LegacyCapGuard {
	return &LegacyCapGuard{Store: st}
}

// CountPending includes every pending invite row regardless of monotonic expiry.
func (g *LegacyCapGuard) CountPending(partyID string) (int, error) {
	var pending int
	err := g.Store.DB().QueryRow(`
SELECT COUNT(1) FROM invites WHERE party_id=? AND status='pending'
`, partyID).Scan(&pending)
	return pending, err
}
