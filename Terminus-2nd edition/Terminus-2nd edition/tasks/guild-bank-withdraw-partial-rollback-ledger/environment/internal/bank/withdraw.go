package bank

import (
	"encoding/json"
	"fmt"

	"github.com/example/vaultcore/internal/model"
)

func (d *DAO) WithdrawStack(guildID, playerID, stackID string, qty int) (model.WithdrawSliceRow, error) {
	if qty <= 0 {
		return model.WithdrawSliceRow{}, fmt.Errorf("invalid quantity")
	}
	stack, err := d.GetStack(stackID)
	if err != nil {
		return model.WithdrawSliceRow{}, err
	}
	if stack.GuildID != guildID {
		return model.WithdrawSliceRow{}, fmt.Errorf("stack guild mismatch")
	}
	if qty > stack.Quantity {
		return model.WithdrawSliceRow{}, fmt.Errorf("quantity exceeds stack")
	}

	mono := d.Clock.NowMonoMs()
	tx, err := d.Store.BeginImmediate()
	if err != nil {
		return model.WithdrawSliceRow{}, err
	}
	defer func() { _ = tx.Rollback() }()

	if qty == stack.Quantity {
		if _, err := tx.Exec(`DELETE FROM item_stacks WHERE stack_id=?`, stackID); err != nil {
			return model.WithdrawSliceRow{}, err
		}
	} else {
		if _, err := tx.Exec(`
UPDATE item_stacks SET quantity = quantity - ? WHERE stack_id=?
`, qty, stackID); err != nil {
			return model.WithdrawSliceRow{}, err
		}
	}

	sliceID := newID("slc_")
	if qty == stack.Quantity {
		if _, err := tx.Exec(`
INSERT INTO withdraw_slices (slice_id, guild_id, player_id, source_stack_id, item_template_id, quantity, created_mono_ms)
VALUES (?, ?, ?, ?, ?, ?, ?)
`, sliceID, guildID, playerID, stackID, stack.ItemTemplateID, qty, mono); err != nil {
			return model.WithdrawSliceRow{}, err
		}
	}

	payload, _ := json.Marshal(map[string]any{
		"player_id": playerID,
		"stack_id":  stackID,
		"quantity":  qty,
	})
	_ = d.WriteAudit(guildID, "withdraw_stack", string(payload), mono)
	if err := tx.Commit(); err != nil {
		return model.WithdrawSliceRow{}, err
	}

	if qty < stack.Quantity {
		return model.WithdrawSliceRow{
			SliceID:        "",
			GuildID:        guildID,
			PlayerID:       playerID,
			SourceStackID:  stackID,
			ItemTemplateID: stack.ItemTemplateID,
			Quantity:       qty,
		}, nil
	}

	return model.WithdrawSliceRow{
		SliceID:        sliceID,
		GuildID:        guildID,
		PlayerID:       playerID,
		SourceStackID:  stackID,
		ItemTemplateID: stack.ItemTemplateID,
		Quantity:       qty,
	}, nil
}
