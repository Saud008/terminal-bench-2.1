package pipeline

import (
	"github.com/terminus/vaultaud/internal/config"
	"github.com/terminus/vaultaud/internal/delegate"
	"github.com/terminus/vaultaud/internal/ledgerbuf"
	"github.com/terminus/vaultaud/internal/lineagewalk"
	"github.com/terminus/vaultaud/internal/model"
	"github.com/terminus/vaultaud/internal/renewchain"
	"github.com/terminus/vaultaud/internal/renewlog"
)

// RunCollect implements the audit stage of the renewal risk pipeline.
func RunCollect(tdir, cdir, stagingPath string) error {
	events, err := renewlog.LoadDir(tdir)
	if err != nil {
		return err
	}
	cfg, err := config.Load(cdir)
	if err != nil {
		return err
	}
	latest := lineagewalk.BuildLatest(events)
	origin := lineagewalk.BuildOrigin(events)

	ctxs := make([]stagedContext, 0, len(events))
	rows := make([]model.StagedLease, 0, len(events))
	for _, ev := range events {
		org, ok := origin[ev.TokenID]
		if !ok {
			org = ev
		}
		staged, err := stageRow(ev, org, latest, cfg)
		if err != nil {
			return err
		}
		ctxs = append(ctxs, staged)
		rows = append(rows, staged.row)
	}
	if err := delegate.Resolve(rows); err != nil {
		return err
	}
	for i := range rows {
		rows[i].EffectiveRenewable = renewchain.Effective(
			rows[i], ctxs[i].event, ctxs[i].ancestors, latest,
			cfg.Mounts, cfg.Roles, ctxs[i].policyDenied,
		)
	}
	return ledgerbuf.Write(stagingPath, rows)
}
