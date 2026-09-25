package interest

import (
	"database/sql"
	"fmt"

	"github.com/example/vaultcore/internal/clock"
	"github.com/example/vaultcore/internal/model"
	"github.com/example/vaultcore/internal/store"
)

type Accrual struct {
	Store *store.Store
	Clock clock.Clock
}

func New(st *store.Store, clk clock.Clock) *Accrual {
	return &Accrual{Store: st, Clock: clk}
}

func (a *Accrual) Run(guildID, periodID string) (model.InterestResult, error) {
	mono := a.Clock.NowMonoMs()
	var rateBps int
	var balance int64
	if err := a.Store.DB().QueryRow(`
SELECT interest_rate_bps, gold_balance FROM guilds WHERE guild_id=?
`, guildID).Scan(&rateBps, &balance); err != nil {
		return model.InterestResult{}, err
	}
	interest := balance * int64(rateBps) / 10000
	if interest <= 0 {
		interest = 1
	}

	tx, err := a.Store.BeginImmediate()
	if err != nil {
		return model.InterestResult{}, err
	}
	defer func() { _ = tx.Rollback() }()

	if _, err := tx.Exec(`
INSERT INTO interest_journal (period_id, guild_id, interest_amount, status, started_mono_ms, finished_mono_ms)
VALUES (?, ?, ?, 'started', ?, 0)
ON CONFLICT(period_id, guild_id) DO NOTHING
`, periodID, guildID, interest, mono); err != nil {
		return model.InterestResult{}, err
	}

	var status string
	var storedInterest int64
	if err := tx.QueryRow(`
SELECT status, interest_amount FROM interest_journal WHERE period_id=? AND guild_id=?
`, periodID, guildID).Scan(&status, &storedInterest); err != nil {
		return model.InterestResult{}, err
	}
	if status == "applied" {
		if err := tx.Commit(); err != nil {
			return model.InterestResult{}, err
		}
		return model.InterestResult{
			GuildID:        guildID,
			PeriodID:       periodID,
			InterestAmount: storedInterest,
			Status:         "applied",
		}, nil
	}

	if _, err := tx.Exec(`
UPDATE guilds SET gold_balance = gold_balance + ? WHERE guild_id=?
`, interest, guildID); err != nil {
		return model.InterestResult{}, err
	}
	if _, err := tx.Exec(`
UPDATE interest_journal SET status='applied', finished_mono_ms=? WHERE period_id=? AND guild_id=?
`, mono, periodID, guildID); err != nil {
		return model.InterestResult{}, err
	}
	if err := tx.Commit(); err != nil {
		return model.InterestResult{}, err
	}
	return model.InterestResult{
		GuildID:        guildID,
		PeriodID:       periodID,
		InterestAmount: interest,
		Status:         "applied",
	}, nil
}

func (a *Accrual) Replay(guildID, periodID string) (model.InterestResult, error) {
	mono := a.Clock.NowMonoMs()
	var interest int64
	var status string
	err := a.Store.DB().QueryRow(`
SELECT interest_amount, status FROM interest_journal
WHERE period_id=? AND guild_id=?
`, periodID, guildID).Scan(&interest, &status)
	if err == sql.ErrNoRows {
		return model.InterestResult{}, fmt.Errorf("journal missing")
	}
	if err != nil {
		return model.InterestResult{}, err
	}
	if status == "applied" {
		return model.InterestResult{
			GuildID:        guildID,
			PeriodID:       periodID,
			InterestAmount: interest,
			Status:         "applied",
		}, nil
	}

	tx, err := a.Store.BeginImmediate()
	if err != nil {
		return model.InterestResult{}, err
	}
	defer func() { _ = tx.Rollback() }()

	if _, err := tx.Exec(`
UPDATE guilds SET gold_balance = gold_balance + ? WHERE guild_id=?
`, interest, guildID); err != nil {
		return model.InterestResult{}, err
	}
	if _, err := tx.Exec(`
UPDATE interest_journal SET status='applied', finished_mono_ms=? WHERE period_id=? AND guild_id=?
`, mono, periodID, guildID); err != nil {
		return model.InterestResult{}, err
	}
	if err := tx.Commit(); err != nil {
		return model.InterestResult{}, err
	}
	return model.InterestResult{
		GuildID:        guildID,
		PeriodID:       periodID,
		InterestAmount: interest,
		Status:         "applied",
	}, nil
}
