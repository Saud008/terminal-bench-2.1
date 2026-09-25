package rules

import (
	"strings"

	"github.com/terminus/sarbctl-curator/internal/model"
)

func CanonicalKey(tool, ruleID string, cat model.RulesCatalog) string {
	t := strings.ToLower(strings.TrimSpace(tool))
	r := strings.TrimSpace(ruleID)
	return t + ":" + r
}
