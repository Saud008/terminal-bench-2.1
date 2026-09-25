package rollupfold

import (
	"sort"
	"strings"

	"github.com/terminus/vaultaud/internal/model"
)

// Edges builds the unique parent-child edge list from parent_id links, not delegated_parent.
func Edges(rows []model.StagedLease) []model.LineageEdge {
	var edges []model.LineageEdge
	seen := map[string]bool{}
	for _, row := range rows {
		if row.ParentID == "" {
			continue
		}
		key := row.ParentID + "->" + row.TokenID
		if seen[key] {
			continue
		}
		seen[key] = true
		edges = append(edges, model.LineageEdge{ParentToken: row.ParentID, ChildToken: row.TokenID})
	}
	sort.Slice(edges, func(i, j int) bool {
		if edges[i].ParentToken != edges[j].ParentToken {
			return edges[i].ParentToken < edges[j].ParentToken
		}
		return edges[i].ChildToken < edges[j].ChildToken
	})
	if edges == nil {
		edges = []model.LineageEdge{}
	}
	return edges
}

// Roots folds staged rows using alphabetical worst_bucket and row-based token counts.
func Roots(rows []model.StagedLease, tokens []model.RiskToken) []model.LineageRootRow {
	type agg struct {
		rowCount int
		maxScore int
		worst    string
		blast    int
	}
	groups := map[string]*agg{}
	for i, row := range rows {
		g := groups[row.LineageRoot]
		if g == nil {
			g = &agg{}
			groups[row.LineageRoot] = g
		}
		g.rowCount++
		if row.LineageDepth > 0 {
			g.blast++
		}
		tok := tokens[i]
		if tok.RiskScore > g.maxScore {
			g.maxScore = tok.RiskScore
		}
		if tok.RiskBucket > g.worst {
			g.worst = tok.RiskBucket
		}
	}
	out := make([]model.LineageRootRow, 0, len(groups))
	for root, g := range groups {
		out = append(out, model.LineageRootRow{
			LineageRoot:  root,
			TokenCount:   g.rowCount,
			RowCount:     g.rowCount,
			MaxRiskScore: g.maxScore,
			WorstBucket:  g.worst,
			BlastRadius:  g.blast,
		})
	}
	sort.Slice(out, func(i, j int) bool {
		return out[i].LineageRoot < out[j].LineageRoot
	})
	if out == nil {
		out = []model.LineageRootRow{}
	}
	return out
}

// Totals builds the rollup totals object from scored tokens.
func Totals(tokens []model.RiskToken) model.RiskTotals {
	seen := map[string]bool{}
	totals := model.RiskTotals{TokenCount: len(tokens)}
	for _, t := range tokens {
		seen[t.TokenID] = true
		if t.IsOrphan {
			totals.OrphanCount++
		}
		if t.RiskBucket == "critical" {
			totals.CriticalCount++
		}
		if t.Admission == model.AdmissionDenied {
			totals.DeniedCount++
		}
		if strings.HasPrefix(t.LineageRoot, model.CyclePrefix) {
			totals.CycleCount++
		}
	}
	totals.DistinctTokenCount = len(seen)
	return totals
}
