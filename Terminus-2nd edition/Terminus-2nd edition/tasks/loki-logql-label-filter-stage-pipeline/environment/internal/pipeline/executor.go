package pipeline

import (
	"sort"
	"strconv"

	"github.com/terminus/lokilogql/internal/format"
	"github.com/terminus/lokilogql/internal/matcher"
	"github.com/terminus/lokilogql/internal/parse"
	"github.com/terminus/lokilogql/internal/types"
	"github.com/terminus/lokilogql/internal/unwrap"
	"github.com/terminus/lokilogql/internal/vector"
)

// ExecuteEval runs the LogQL pipeline and returns stage output.
func ExecuteEval(lines []types.LogLine, ast types.QueryAST) (*types.StageFile, error) {
	rows := make([]types.WorkingRow, len(lines))
	insertOrder := []string{}
	seenLabel := map[string]bool{}
	for i, ln := range lines {
		labels := map[string]string{}
		for k, v := range ln.Labels {
			labels[k] = v
			if !seenLabel[k] {
				seenLabel[k] = true
				insertOrder = append(insertOrder, k)
			}
		}
		rows[i] = types.WorkingRow{Labels: labels, Fields: map[string]string{}, Value: 1}
	}

	var groupBy []string
	jsonStages := []types.QueryStage{}
	otherStages := []types.QueryStage{}
	for _, st := range ast.Stages {
		if st.Kind == "json" {
			jsonStages = append(jsonStages, st)
		} else {
			otherStages = append(otherStages, st)
		}
	}
	ordered := append(jsonStages, otherStages...)

	for _, st := range ordered {
		switch st.Kind {
		case "json":
			for i := range rows {
				if rows[i].Filtered {
					continue
				}
				_ = parse.ParseJSON(lines[i].Line, rows[i].Fields)
				for k, v := range rows[i].Fields {
					rows[i].Labels[k] = v
				}
			}
		case "matcher":
			matcher.ApplyMatcher(rows, st.Selector)
		case "line_format":
			for i := range rows {
				if rows[i].Filtered {
					continue
				}
				formatted := format.ApplyLineFormat(st.Template, rows[i].Fields)
				rows[i].Fields["line"] = formatted
				rows[i].Fields["width"] = strconv.Itoa(len(formatted))
			}
		case "unwrap":
			for i := range rows {
				if rows[i].Filtered {
					continue
				}
				rows[i].Value = unwrap.ApplyUnwrap(rows[i].Labels, rows[i].Fields, st.Field)
			}
		case "sum_by":
			groupBy = st.GroupBy
		}
	}

	vectors, selected := vector.GroupSum(rows, groupBy, insertOrder)
	sort.Slice(vectors, func(i, j int) bool {
		return vectors[i].Checksum < vectors[j].Checksum
	})

	return &types.StageFile{
		Query:               ast,
		LabelInsertOrder:    insertOrder,
		Vectors:             vectors,
		SelectedGroupLabels: selected,
	}, nil
}
