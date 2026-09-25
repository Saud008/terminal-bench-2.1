package bank

import (
	"encoding/json"
	"fmt"
)

func (d *DAO) TransferOut(guildID, playerID, stackID string) (string, error) {
	stack, err := d.GetStack(stackID)
	if err != nil {
		return "", err
	}
	if stack.GuildID != guildID {
		return "", fmt.Errorf("stack guild mismatch")
	}

	mono := d.Clock.NowMonoMs()
	tx, err := d.Store.BeginImmediate()
	if err != nil {
		return "", err
	}
	defer func() { _ = tx.Rollback() }()

	playerStackID := newID("pst_")
	if _, err := tx.Exec(`
INSERT INTO player_stacks (stack_id, guild_id, player_id, item_template_id, quantity, bound, created_mono_ms)
VALUES (?, ?, ?, ?, ?, ?, ?)
`, playerStackID, guildID, playerID, stack.ItemTemplateID, stack.Quantity, boolToInt(stack.Bound), mono); err != nil {
		return "", err
	}
	if _, err := tx.Exec(`DELETE FROM item_stacks WHERE stack_id=?`, stackID); err != nil {
		return "", err
	}

	payload, _ := json.Marshal(map[string]any{
		"player_id":       playerID,
		"stack_id":        stackID,
		"player_stack_id": playerStackID,
	})
	_ = d.WriteAudit(guildID, "transfer_out", string(payload), mono)
	if err := tx.Commit(); err != nil {
		return "", err
	}
	return playerStackID, nil
}

func boolToInt(v bool) int {
	if v {
		return 1
	}
	return 0
}
