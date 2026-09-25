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

// Resolve folds every attached policy chain into the tightest cap and the renewal denial flag.
func Resolve(names []string, pol model.PoliciesFile, at time.Time) (Resolved, error) {
	if len(names) == 0 {
		return Resolved{}, policyError("no policies on token")
	}
	out := Resolved{CapSec: unbounded}
	for _, name := range names {
		cap, deny, err := chainCap(name, pol, at)
		if err != nil {
			return Resolved{}, err
		}
		if cap < out.CapSec {
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
		if rev.OverrideParent {
			return rev.MaxTTLSec, deny, nil
		}
		if rev.MaxTTLSec < cap {
			cap = rev.MaxTTLSec
		}
		cur = rev.Parent
	}
	return cap, deny, nil
}

type policyError string

func (e policyError) Error() string { return string(e) }
