package atlasemit

import (
	"encoding/json"
	"os"
	"sort"
	"time"

	"github.com/terminus/vaultaud/internal/model"
	"github.com/terminus/vaultaud/internal/riskbands"
	"github.com/terminus/vaultaud/internal/rollupfold"
)

// WriteAtlas scores every staged row and folds the full rollup document.
func WriteAtlas(rows []model.StagedLease, anchor time.Time, reportPath string) error {
	tokens := make([]model.RiskToken, len(rows))
	for i, row := range rows {
		tokens[i] = riskbands.Score(row, anchor)
	}
	sort.SliceStable(tokens, func(i, j int) bool {
		if tokens[i].TokenID != tokens[j].TokenID {
			return tokens[i].TokenID < tokens[j].TokenID
		}
		return tokens[i].RenewalSeq < tokens[j].RenewalSeq
	})
	// Re-score in staging order so Roots can pair by index.
	scoredInOrder := make([]model.RiskToken, len(rows))
	for i, row := range rows {
		scoredInOrder[i] = riskbands.Score(row, anchor)
	}
	rep := model.RiskAtlas{
		Tokens:       tokens,
		LineageEdges: rollupfold.Edges(rows),
		LineageRoots: rollupfold.Roots(rows, scoredInOrder),
		Totals:       rollupfold.Totals(tokens),
	}
	b, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(reportPath, append(b, '\n'), 0o644)
}
