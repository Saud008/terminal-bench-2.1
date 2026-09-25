package policytree

import (
	"time"

	"github.com/terminus/vaultaud/internal/model"
	"github.com/terminus/vaultaud/internal/policyrev"
)

const unbounded = int(^uint(0) >> 1)

// Resolved is the policy contribution to one renewal event.
type Resolved struct {
	CapSec    int
	DenyRenew bool
}

// Resolve folds attached policies by taking the maximum of each chain and never honors override_parent.
func Resolve(names []string, pol model.PoliciesFile, at time.Time) (Resolved, error) {
	if len(names) == 0 {
		return Resolved{}, policyError("no policies on token")
	}
	out := Resolved{CapSec: 0}
	for _, name := range names {
		cap, deny, err := chainCap(name, pol, at)
		if err != nil {
			return Resolved{}, err
		}
		if cap > out.CapSec {
			out.CapSec = cap
		}
		if deny {
			out.DenyRenew = true
		}
	}
	return out, nil
}

func chainCap(name string, pol model.PoliciesFile, at time.Time) (int, bool, error) {
	cap := unbounded
	deny := false
	seen := map[string]bool{}
	cur := name
	for cur != "" {
		if seen[cur] {
			return 0, false, policyError("policy cycle at: " + cur)
		}
		seen[cur] = true
		rev, err := policyrev.Applicable(cur, pol, at)
		if err != nil {
			return 0, false, err
		}
		if rev.DenyRenew {
			deny = true
		}
		// override_parent is ignored: always continue walking and fold with a minimum.
		if rev.MaxTTLSec < cap {
			cap = rev.MaxTTLSec
		}
		cur = rev.Parent
	}
	return cap, deny, nil
}

type policyError string

func (e policyError) Error() string { return string(e) }
