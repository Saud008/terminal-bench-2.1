package pipeline

import (
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/chmutled/internal/config"
	"github.com/terminus/chmutled/internal/ledgerbuf"
	"github.com/terminus/chmutled/internal/model"
	"github.com/terminus/chmutled/internal/sqlledger"
)

// RunEmit is the export stage that persists SQLite rows and writes the readiness atlas.
func RunEmit(stagingPath, sqlitePath, atlasPath string) error {
	rows, err := ledgerbuf.Read(stagingPath)
	if err != nil {
		return err
	}
	db, err := sqlledger.Open(sqlitePath)
	if err != nil {
		return err
	}
	defer db.Close()
	if err := sqlledger.Upsert(db, rows); err != nil {
		return err
	}
	cfg, err := config.Load("/app/fixtures/config")
	if err != nil {
		return cfgLoadErr(err)
	}
	report := buildReport(rows, cfg.Anchor)
	sort.Slice(report.Mutations, func(i, j int) bool {
		if report.Mutations[i].PartitionID != report.Mutations[j].PartitionID {
			return report.Mutations[i].PartitionID < report.Mutations[j].PartitionID
		}
		return report.Mutations[i].MutationVersion < report.Mutations[j].MutationVersion
	})
	b, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	b = append(b, '\n')
	return os.WriteFile(atlasPath, b, 0o644)
}

type cfgErr struct{ err error }

func cfgLoadErr(e error) error { return cfgErr{e} }
func (e cfgErr) Error() string  { return e.err.Error() }

func buildReport(rows []model.StagedMutation, anchor string) model.ReadinessReport {
	rep := model.ReadinessReport{AnchorUTC: anchor, Mutations: append([]model.StagedMutation(nil), rows...)}
	for _, r := range rows {
		rep.Totals.MutationCount++
		switch r.ReadinessState {
		case "ready":
			rep.Totals.ReadyCount++
		case "suppressed":
			rep.Totals.SuppressedCount++
		case "detached":
			rep.Totals.DetachedCount++
		}
	}
	return rep
}
