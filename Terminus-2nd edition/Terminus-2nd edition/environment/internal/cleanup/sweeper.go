package cleanup

import (
	"github.com/terminus/party-invite/internal/clock"
	"github.com/terminus/party-invite/internal/store"
)

type Sweeper struct {
	Store *store.Store
	Clock clock.Clock
}

func New(st *store.Store, clk clock.Clock) *Sweeper {
	return &Sweeper{Store: st, Clock: clk}
}

// SweepResult is the JSON body of POST /v1/admin/sweep.
// Contract: /app/docs/sweep-contract.md
type SweepResult struct {
	ExpiredInvites int `json:"expired_invites"`
	RemovedParties int `json:"removed_parties"`
}

// Run expires invites and drops orphan parties. Audit staging refresh is not wired yet — see
// /app/docs/sweep-contract.md for the epoch, refresh, and retirement steps a sweep owes the ledger.
func (s *Sweeper) Run() (SweepResult, error) {
	monoMs := s.Clock.NowMonoMs()
	res, err := s.Store.DB().Exec(`
UPDATE invites SET status='expired'
WHERE status='pending' AND expires_mono_ms <= ?
`, monoMs)
	if err != nil {
		return SweepResult{}, err
	}
	expired, _ := res.RowsAffected()

	removedRes, err := s.Store.DB().Exec(`
DELETE FROM parties WHERE status='disbanded' AND party_id NOT IN (
    SELECT DISTINCT party_id FROM members WHERE status='connected'
)
`)
	if err != nil {
		return SweepResult{}, err
	}
	removed, _ := removedRes.RowsAffected()

	return SweepResult{
		ExpiredInvites: int(expired),
		RemovedParties: int(removed),
	}, nil
}
