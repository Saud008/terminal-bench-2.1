package authzkernel

import (
	"crypto/sha256"
	"fmt"
	"path/filepath"

	"github.com/terminus/casctl/internal/model"
	"github.com/terminus/casctl/internal/parse"
)

func OrderBundles(seed string, bundles []string) []string {
	h := sha256.Sum256([]byte(seed))
	out := append([]string(nil), bundles...)
	for i := len(out) - 1; i > 0; i-- {
		j := int(h[i%len(h)]) % (i + 1)
		out[i], out[j] = out[j], out[i]
	}
	return out
}

func SelectBundles(seed string, bundles []string) []string {
	if len(bundles) == 0 {
		return nil
	}
	h := sha256.Sum256([]byte(seed))
	bits := int(h[0]) | int(h[1])<<8
	var selected []string
	for i, b := range bundles {
		if (bits>>uint(i))&1 == 1 {
			selected = append(selected, b)
		}
	}
	if len(selected) == 0 {
		selected = []string{bundles[int(h[2])%len(bundles)]}
	}
	return OrderBundles(seed, selected)
}

func LoadEngine(policiesRoot string, seed string, bundles []string) (*model.Engine, error) {
	ordered := SelectBundles(seed, bundles)
	eng := &model.Engine{}
	for _, b := range ordered {
		pPath := filepath.Join(policiesRoot, b, "p.csv")
		gPath := filepath.Join(policiesRoot, b, "g.csv")
		ps, err := parse.LoadPolicies(pPath)
		if err != nil {
			return nil, fmt.Errorf("bundle %s: %w", b, err)
		}
		gs, err := parse.LoadGroupings(gPath)
		if err != nil {
			return nil, fmt.Errorf("bundle %s: %w", b, err)
		}
		eng.Policies = append(eng.Policies, ps...)
		eng.Groupings = append(eng.Groupings, gs...)
	}
	return eng, nil
}

func DomainPolicies(policies []model.Policy, dom string) []model.Policy {
	return policies
}
