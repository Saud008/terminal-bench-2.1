package rules

import (
	"regexp"
	"strings"

	"github.com/terminus/sarbctl-curator/internal/model"
)

var (
	atVer = regexp.MustCompile(`@v[0-9]+$`)
	slash = regexp.MustCompile(`/v[0-9]+$`)
)

func CanonicalKey(tool, ruleID string, cat model.RulesCatalog) string {
	t := strings.ToLower(strings.TrimSpace(tool))
	r := strings.TrimSpace(ruleID)
	if cat.Aliases != nil {
		if alt, ok := cat.Aliases[r]; ok {
			r = alt
		}
	}
	r = atVer.ReplaceAllString(r, "")
	r = slash.ReplaceAllString(r, "")
	return t + ":" + r
}
