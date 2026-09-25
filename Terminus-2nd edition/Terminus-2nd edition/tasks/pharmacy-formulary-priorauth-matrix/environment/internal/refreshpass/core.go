package refreshpass

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/formulatrix/internal/formndc"
	"github.com/terminus/formulatrix/internal/model"
	"github.com/terminus/formulatrix/internal/planrule"
	"github.com/terminus/formulatrix/internal/rosterfreeze"
	"github.com/terminus/formulatrix/internal/store"
)

const genPath = "/app/state/refresh-revision.json"

func Run(scenario string) error {
	stage, err := rosterfreeze.ReadRoster("")
	if err != nil {
		return err
	}
	rows := buildRows(stage)
	db, err := store.Open("")
	if err != nil {
		return err
	}
	defer db.Close()
	if err := store.InsertRows(db, rows); err != nil {
		return err
	}
	return bumpRevision()
}

func buildRows(stage model.RosterFile) []model.MatrixRow {
	var rows []model.MatrixRow
	for _, plan := range stage.Plans {
		paByNDC := map[string]bool{}
		for _, drug := range stage.Drugs {
			paByNDC[formndc.NormalizeNDC(drug.NDC)] = true
		}
		for _, drug := range stage.Drugs {
			ndc := formndc.NormalizeNDC(drug.NDC)
			if ovr, ok := planrule.SelectOverride(stage.Overrides, plan.PlanID, drug.NDC, stage.AsOf); ok {
				paByNDC[ndc] = ovr.PaRequired
			}
		}
		for _, drug := range stage.Drugs {
			ndc := formndc.NormalizeNDC(drug.NDC)
			rx := formndc.PreferredRxNorm(drug)
			requiresPA := paByNDC[ndc]
			overrideApplied := false
			effectiveRule := "baseline"
			if ovr, ok := planrule.SelectOverride(stage.Overrides, plan.PlanID, drug.NDC, stage.AsOf); ok {
				requiresPA = ovr.PaRequired
				overrideApplied = true
				effectiveRule = ovr.EffectiveStart
			}
			stepOK := planrule.StepComplete(stage.StepChains, plan.PlanID, drug.NDC, paByNDC)
			rows = append(rows, model.MatrixRow{
				PlanID:          plan.PlanID,
				NDCNormalized:   ndc,
				PreferredRxNorm: rx,
				RequiresPA:      requiresPA,
				StepComplete:    stepOK,
				OverrideApplied: overrideApplied,
				EffectiveRule:   effectiveRule,
			})
		}
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].PlanID != rows[j].PlanID {
			return rows[i].PlanID < rows[j].PlanID
		}
		return rows[i].NDCNormalized < rows[j].NDCNormalized
	})
	return rows
}

func bumpRevision() error {
	var gen model.RevisionFile
	if raw, err := os.ReadFile(genPath); err == nil {
		_ = json.Unmarshal(raw, &gen)
	}
	gen.RefreshRevision = gen.RefreshRevision + 1
	data, err := json.MarshalIndent(gen, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	if err := os.MkdirAll(filepath.Dir(genPath), 0o755); err != nil {
		return err
	}
	return os.WriteFile(genPath, data, 0o644)
}
