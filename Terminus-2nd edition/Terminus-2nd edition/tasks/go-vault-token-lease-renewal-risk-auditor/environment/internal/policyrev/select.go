package policyrev

import (
	"time"

	"github.com/terminus/vaultaud/internal/model"
)

type revError string

func (e revError) Error() string { return string(e) }

// Applicable returns the first revision whose effective_from is strictly before at.
// Later revisions and equal-boundary revisions are ignored.
func Applicable(name string, pol model.PoliciesFile, at time.Time) (model.PolicyRevision, error) {
	def, ok := pol.Policies[name]
	if !ok {
		return model.PolicyRevision{}, revError("unknown policy: " + name)
	}
	for _, rev := range def.Revisions {
		from, err := time.Parse(time.RFC3339, rev.EffectiveFrom)
		if err != nil {
			return model.PolicyRevision{}, revError("bad effective_from on policy: " + name)
		}
		if from.Before(at) {
			return rev, nil
		}
	}
	return model.PolicyRevision{}, revError("no applicable revision for policy: " + name)
}
