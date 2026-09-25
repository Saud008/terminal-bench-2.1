package bank

import (
	"fmt"

	"github.com/example/vaultcore/internal/config"
	"github.com/example/vaultcore/internal/model"
)

type Handler struct {
	dao *DAO
	cfg config.Config
}

func NewHandler(dao *DAO, cfg config.Config) *Handler {
	return &Handler{dao: dao, cfg: cfg}
}

func (h *Handler) Bootstrap(guildID string, initialGold int64, rateBps *int) (model.GuildRow, error) {
	if guildID == "" {
		return model.GuildRow{}, fmt.Errorf("guild_id required")
	}
	if initialGold < 0 {
		return model.GuildRow{}, fmt.Errorf("initial_gold invalid")
	}
	rate := h.cfg.DefaultInterestRateBps
	if rateBps != nil {
		rate = *rateBps
	}
	return h.dao.Bootstrap(guildID, initialGold, rate)
}

func (h *Handler) DepositStack(guildID, templateID string, qty int, bound *bool) (model.StackRow, error) {
	isBound := false
	if bound != nil {
		isBound = *bound
	}
	return h.dao.DepositStack(guildID, templateID, qty, isBound)
}

func (h *Handler) WithdrawGold(guildID, playerID string, amount int64) (int64, error) {
	return h.dao.WithdrawGold(guildID, playerID, amount)
}

func (h *Handler) WithdrawStack(guildID, playerID, stackID string, qty int) (model.WithdrawSliceRow, error) {
	return h.dao.WithdrawStack(guildID, playerID, stackID, qty)
}

func (h *Handler) TransferOut(guildID, playerID, stackID string) (string, error) {
	return h.dao.TransferOut(guildID, playerID, stackID)
}

func (h *Handler) Export(guildID string) (model.AuditReport, error) {
	return h.dao.BuildAudit(guildID)
}
