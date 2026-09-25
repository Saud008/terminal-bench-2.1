package matcher

import "github.com/terminus/lokilogql/internal/types"

// MatchSelector returns true when every selector key equals the line labels.
func MatchSelector(labels map[string]string, sel map[string]string) bool {
	for k, want := range sel {
		if labels[k] != want {
			return false
		}
	}
	return true
}

func ApplyMatcher(rows []types.WorkingRow, sel map[string]string) {
	for i := range rows {
		if !MatchSelector(rows[i].Labels, sel) {
			rows[i].Filtered = true
		}
	}
}
