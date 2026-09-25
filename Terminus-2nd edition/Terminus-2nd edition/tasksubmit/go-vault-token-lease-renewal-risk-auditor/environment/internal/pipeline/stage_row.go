package pipeline

import (
	"time"

	"github.com/terminus/vaultaud/internal/budgetclamp"
	"github.com/terminus/vaultaud/internal/config"
	"github.com/terminus/vaultaud/internal/lineagewalk"
	"github.com/terminus/vaultaud/internal/model"
	"github.com/terminus/vaultaud/internal/policytree"
	"github.com/terminus/vaultaud/internal/ttlcascade"
)

// stagedContext carries the per-event facts that the staged row itself does not record.
type stagedContext struct {
	row          model.StagedLease
	event        model.RenewalEvent
	ancestors    []string
	policyDenied bool
}

// stageRow resolves everything about one renewal that does not depend on other staged rows.
func stageRow(ev model.RenewalEvent, origin model.RenewalEvent,
	latest map[string]model.RenewalEvent, cfg *config.Bundle) (stagedContext, error) {
	issued, err := time.Parse(time.RFC3339, ev.IssuedAt)
	if err != nil {
		return stagedContext{}, err
	}
	pol, err := policytree.Resolve(ev.PolicyNames, cfg.Policies, issued)
	if err != nil {
		return stagedContext{}, err
	}
	static, err := ttlcascade.StaticCap(ev, pol.CapSec, cfg.Mounts, cfg.Roles)
	if err != nil {
		return stagedContext{}, err
	}
	budget, err := budgetclamp.Resolve(ev, origin, cfg.Mounts, cfg.Roles)
	if err != nil {
		return stagedContext{}, err
	}
	lin := lineagewalk.Resolve(ev, latest)
	row := model.StagedLease{
		EventID:            ev.EventID,
		TokenID:            ev.TokenID,
		ParentID:           ev.ParentID,
		RenewalSeq:         ev.RenewalSeq,
		Mount:              ev.Mount,
		Role:               ev.Role,
		PolicyCapSec:       pol.CapSec,
		StaticCapSec:       static,
		LifetimeCeilingSec: budget.CeilingSec,
		BudgetRemainingSec: budget.RemainingSec,
		DelegatedParent:    lin.DelegatedParent,
		LineageRoot:        lin.LineageRoot,
		LineageDepth:       lin.LineageDepth,
		IsOrphan:           lin.IsOrphan,
		IssuedAt:           ev.IssuedAt,
	}
	return stagedContext{row: row, event: ev, ancestors: lin.Ancestors, policyDenied: pol.DenyRenew}, nil
}
