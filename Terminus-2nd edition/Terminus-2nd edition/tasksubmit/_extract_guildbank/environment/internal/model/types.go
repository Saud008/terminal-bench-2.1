package model

type BootstrapRequest struct {
	GuildID         string `json:"guild_id"`
	InitialGold     int64  `json:"initial_gold"`
	InterestRateBps *int   `json:"interest_rate_bps,omitempty"`
}

type DepositStackRequest struct {
	ItemTemplateID string `json:"item_template_id"`
	Quantity       int    `json:"quantity"`
	Bound          *bool  `json:"bound,omitempty"`
}

type WithdrawGoldRequest struct {
	PlayerID string `json:"player_id"`
	Amount   int64  `json:"amount"`
}

type WithdrawStackRequest struct {
	PlayerID string `json:"player_id"`
	StackID  string `json:"stack_id"`
	Quantity int    `json:"quantity"`
}

type TransferOutRequest struct {
	PlayerID string `json:"player_id"`
	StackID  string `json:"stack_id"`
}

type InterestRequest struct {
	GuildID  string `json:"guild_id"`
	PeriodID string `json:"period_id"`
}

type ExportRequest struct {
	GuildID string `json:"guild_id"`
}

type GuildRow struct {
	GuildID         string
	GoldBalance     int64
	InterestRateBps int
}

type StackRow struct {
	StackID        string
	GuildID        string
	ItemTemplateID string
	Quantity       int
	Bound          bool
}

type WithdrawSliceRow struct {
	SliceID        string
	GuildID        string
	PlayerID       string
	SourceStackID  string
	ItemTemplateID string
	Quantity       int
}

type AuditReport struct {
	GuildID              string `json:"guild_id"`
	GoldBalance          int64  `json:"gold_balance"`
	VaultStackQty        int    `json:"vault_stack_qty"`
	WithdrawnSliceQty    int    `json:"withdrawn_slice_qty"`
	CommittedAuditCount  int    `json:"committed_audit_count"`
	OrphanAuditCount     int    `json:"orphan_audit_count"`
	InterestAppliedTotal int64  `json:"interest_applied_total"`
}

type InterestResult struct {
	GuildID        string `json:"guild_id"`
	PeriodID       string `json:"period_id"`
	InterestAmount int64  `json:"interest_amount"`
	Status         string `json:"status"`
}
