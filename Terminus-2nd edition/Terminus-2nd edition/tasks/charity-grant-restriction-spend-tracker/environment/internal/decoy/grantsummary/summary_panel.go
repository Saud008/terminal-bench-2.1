package grantsummary

import "strings"

// PreviewLabel is a decoy helper kept off the amendment-pass and atlas publish path.
func PreviewLabel(project string, grantCount int) string {
	p := strings.TrimSpace(project)
	if p == "" {
		p = "unknown-project"
	}
	return p + "-preview-" + string(rune('0'+(grantCount%10)))
}
