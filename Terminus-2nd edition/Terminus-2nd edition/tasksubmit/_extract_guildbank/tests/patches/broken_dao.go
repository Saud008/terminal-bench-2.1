package bank

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"

	"github.com/example/vaultcore/internal/clock"
	"github.com/example/vaultcore/internal/config"
	"github.com/example/vaultcore/internal/model"
	"github.com/example/vaultcore/internal/store"
)

type DAO struct {
	Store *store.Store
	Clock clock.Clock
	Cfg   config.Config
}

func NewDAO(st *store.Store, clk clock.Clock, cfg config.Config) *DAO {
	return &DAO{Store: st, Clock: clk, Cfg: cfg}
}

func newID(prefix string) string {
	buf := make([]byte, 8)
	_, _ = rand.Read(buf)
	return prefix + hex.EncodeToString(buf)
}

func (d *DAO) Bootstrap(guildID string, initialGold int64, rateBps int) (model.GuildRow, error) {
	mono := d.Clock.NowMonoMs()
	_, err := d.Store.DB().Exec(`
INSERT INTO guilds (guild_id, gold_balance, interest_rate_bps, created_mono_ms)
VALUES (?, ?, ?, ?)
`, guildID, initialGold, rateBps, mono)
	if err != nil {
		return model.GuildRow{}, err
	}
	return model.GuildRow{GuildID: guildID, GoldBalance: initialGold, InterestRateBps: rateBps}, nil
}

func (d *DAO) GetGuild(guildID string) (model.GuildRow, error) {
	row := d.Store.DB().QueryRow(`
SELECT guild_id, gold_balance, interest_rate_bps FROM guilds WHERE guild_id=?
`, guildID)
	var g model.GuildRow
	if err := row.Scan(&g.GuildID, &g.GoldBalance, &g.InterestRateBps); err != nil {
		return model.GuildRow{}, err
	}
	return g, nil
}

func (d *DAO) DepositStack(guildID, templateID string, qty int, bound bool) (model.StackRow, error) {
	if qty <= 0 || qty > d.Cfg.MaxStackQuantity {
		return model.StackRow{}, fmt.Errorf("invalid quantity")
	}
	boundInt := 0
	if bound {
		boundInt = 1
	}
	stackID := newID("stk_")
	_, err := d.Store.DB().Exec(`
INSERT INTO item_stacks (stack_id, guild_id, item_template_id, quantity, bound)
VALUES (?, ?, ?, ?, ?)
`, stackID, guildID, templateID, qty, boundInt)
	if err != nil {
		return model.StackRow{}, err
	}
	return model.StackRow{
		StackID:        stackID,
		GuildID:        guildID,
		ItemTemplateID: templateID,
		Quantity:       qty,
		Bound:          bound,
	}, nil
}

func (d *DAO) GetStack(stackID string) (model.StackRow, error) {
	row := d.Store.DB().QueryRow(`
SELECT stack_id, guild_id, item_template_id, quantity, bound FROM item_stacks WHERE stack_id=?
`, stackID)
	var s model.StackRow
	var bound int
	if err := row.Scan(&s.StackID, &s.GuildID, &s.ItemTemplateID, &s.Quantity, &bound); err != nil {
		return model.StackRow{}, err
	}
	s.Bound = bound == 1
	return s, nil
}

func (d *DAO) WithdrawGold(guildID, playerID string, amount int64) (int64, error) {
	if amount <= 0 {
		return 0, fmt.Errorf("invalid amount")
	}
	mono := d.Clock.NowMonoMs()
	tx, err := d.Store.BeginImmediate()
	if err != nil {
		return 0, err
	}
	defer func() { _ = tx.Rollback() }()

	var balance int64
	if err := tx.QueryRow(`SELECT gold_balance FROM guilds WHERE guild_id=?`, guildID).Scan(&balance); err != nil {
		return 0, err
	}
	if balance < amount {
		failPayload, _ := json.Marshal(map[string]any{"player_id": playerID, "amount": amount})
		_ = d.WriteAudit(guildID, "withdraw_gold", string(failPayload), mono)
		return 0, fmt.Errorf("insufficient gold")
	}
	newBal := balance - amount
	if _, err := tx.Exec(`UPDATE guilds SET gold_balance=? WHERE guild_id=?`, newBal, guildID); err != nil {
		return 0, err
	}

	payload, _ := json.Marshal(map[string]any{
		"player_id": playerID,
		"amount":    amount,
		"balance":   newBal,
	})
	_ = d.WriteAudit(guildID, "withdraw_gold", string(payload), mono)
	if err := tx.Commit(); err != nil {
		return 0, err
	}
	return newBal, nil
}

func (d *DAO) WriteAudit(guildID, opType, payload string, mono int64) error {
	entryID := newID("aud_")
	_, err := d.Store.DB().Exec(`
INSERT INTO audit_entries (entry_id, guild_id, op_type, payload_json, committed, mono_ms)
VALUES (?, ?, ?, ?, 1, ?)
`, entryID, guildID, opType, payload, mono)
	return err
}

func (d *DAO) BuildAudit(guildID string) (model.AuditReport, error) {
	guild, err := d.GetGuild(guildID)
	if err != nil {
		return model.AuditReport{}, err
	}
	vaultQty, err := d.Store.VaultStackQty(guildID)
	if err != nil {
		return model.AuditReport{}, err
	}
	sliceQty, err := d.Store.WithdrawnSliceQty(guildID)
	if err != nil {
		return model.AuditReport{}, err
	}
	committed, orphan, err := d.Store.CountAudit(guildID)
	if err != nil {
		return model.AuditReport{}, err
	}
	interestTotal, err := d.Store.InterestAppliedTotal(guildID)
	if err != nil {
		return model.AuditReport{}, err
	}
	return model.AuditReport{
		GuildID:              guildID,
		GoldBalance:          guild.GoldBalance,
		VaultStackQty:        vaultQty,
		WithdrawnSliceQty:    sliceQty,
		CommittedAuditCount:  committed,
		OrphanAuditCount:     orphan,
		InterestAppliedTotal: interestTotal,
	}, nil
}
