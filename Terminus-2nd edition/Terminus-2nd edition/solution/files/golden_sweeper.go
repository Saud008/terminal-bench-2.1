package cleanup

import (
	"github.com/terminus/party-invite/internal/clock"
	"github.com/terminus/party-invite/internal/party"
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
	RetiredParties int `json:"retired_parties"`
	SweepEpoch     int `json:"sweep_epoch"`
}

// Run expires invites on the monotonic clock, drops orphan parties, then advances the audit ledger
// epoch and refreshes staging before the next published report.
// Contract: /app/docs/sweep-contract.md
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

	epoch, err := party.MarkSweepEpoch()
	if err != nil {
		return SweepResult{}, err
	}
	retired, err := party.RefreshSnapshotsAfterSweep(s.Store, s.Clock, monoMs)
	if err != nil {
		return SweepResult{}, err
	}

	return SweepResult{
		ExpiredInvites: int(expired),
		RemovedParties: int(removed),
		RetiredParties: retired,
		SweepEpoch:     epoch,
	}, nil
}
