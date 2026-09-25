package scan

import (
	"fmt"
	"os"

	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/export"
	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/model"
	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/page"
	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/parallel"
	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/parse"
	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/planner"
	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/staging"
	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/stats"
	"github.com/terminus/duckdb-parquet-pushdown-null-filter/internal/timezone"
)

func FilterCatalog(catalogPath, outputPath string, spec model.FilterSpec) error {
	cat, err := parse.LoadCatalog(catalogPath)
	if err != nil {
		return err
	}
	if spec.Workers <= 0 {
		spec.Workers = 1
	}

	selected, pruned := planner.SelectRowGroups(cat, spec)
	selected, statsPruned := stats.FilterRowGroupsByStats(cat, selected, spec.TsGte)
	pruned = append(pruned, statsPruned...)

	slices := parallel.BuildWorkerSlices(cat, selected, spec.Workers)
	plan := model.PushdownPlan{
		Table:          cat.Table,
		SelectedGroups: selected,
		PageReadOrder:  []string{"null_bitmap", "dictionary", "data"},
		WorkerSlices:   slices,
		PlanWritten:    true,
	}
	if err := staging.WritePlan(plan); err != nil {
		return err
	}

	matched := map[int]struct{}{}
	for _, gid := range selected {
		rg := findGroup(cat, gid)
		for _, slice := range parallel.SplitRowGroup(rg, spec.Workers) {
			rows := parallel.RowsForSlice(rg, slice)
			for _, row := range rows {
				if spec.TsGte != "" && !timezone.MeetsTsGte(row.MeasuredAt, spec.TsGte, cat.CatalogTZ) {
					continue
				}
				if spec.IsNullCol != "" {
					hits := page.ReadPages(rg, spec.IsNullCol, true)
					ok := false
					for _, h := range hits {
						if h.RowID == row.RowID {
							ok = true
							break
						}
					}
					if !ok {
						continue
					}
				}
				matched[row.RowID] = struct{}{}
			}
		}
	}

	ids := make([]int, 0, len(matched))
	for id := range matched {
		ids = append(ids, id)
	}
	res := export.BuildResult(cat, ids, pruned, plan)
	return export.WriteResult(outputPath, res)
}

func findGroup(cat model.Catalog, id int) model.RowGroup {
	for _, rg := range cat.RowGroups {
		if rg.ID == id {
			return rg
		}
	}
	return model.RowGroup{}
}

func FilterCLI(catalogPath, outputPath string, spec model.FilterSpec) int {
	if _, err := os.Stat(catalogPath); err != nil {
		fmt.Fprintf(os.Stderr, "catalog not found: %s\n", catalogPath)
		return 2
	}
	if err := FilterCatalog(catalogPath, outputPath, spec); err != nil {
		fmt.Fprintf(os.Stderr, "filter failed: %v\n", err)
		return 3
	}
	return 0
}
