package policyrev

import (
	"time"

	"github.com/terminus/vaultaud/internal/model"
)

type revError string

func (e revError) Error() string { return string(e) }

// Applicable returns the revision of name in force at at: the greatest effective_from that is
// not after at, later list entries winning ties.
func Applicable(name string, pol model.PoliciesFile, at time.Time) (model.PolicyRevision, error) {
	def, ok := pol.Policies[name]
	if !ok {
		return model.PolicyRevision{}, revError("unknown policy: " + name)
	}
	var best model.PolicyRevision
	var bestAt time.Time
	found := false
	for _, rev := range def.Revisions {
		from, err := time.Parse(time.RFC3339, rev.EffectiveFrom)
		if err != nil {
			return model.PolicyRevision{}, revError("bad effective_from on policy: " + name)
		}
		if from.After(at) {
			continue
		}
		if !found || !from.Before(bestAt) {
			best, bestAt, found = rev, from, true
		}
	}
	if !found {
		return model.PolicyRevision{}, revError("no applicable revision for policy: " + name)
	}
	return best, nil
}
