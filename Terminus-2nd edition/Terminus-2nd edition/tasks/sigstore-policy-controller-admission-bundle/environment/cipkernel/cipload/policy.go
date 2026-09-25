package cipload

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/slsacip/cipkernel/ciptypes"
)

type buildersFile struct {
	Deny    []string `json:"deny"`
	Require []string `json:"require"`
}

type digestDenyFile struct {
	DenyDigests []string `json:"deny_digests"`
}

type predicatesFile struct {
	Allow []string `json:"allow"`
}

type revocationsFile struct {
	Revocations []ciptypes.Revocation `json:"revocations"`
}

// LoadPolicyPack reads the four fixture files that make up a named policy
// pack directory under root: builders.json, digest-deny.json,
// predicates.json, and revocations.json.
func LoadPolicyPack(root, name string) (ciptypes.PolicyPack, error) {
	dir := filepath.Join(root, name)

	var builders buildersFile
	if err := readJSON(filepath.Join(dir, "builders.json"), &builders); err != nil {
		return ciptypes.PolicyPack{}, err
	}
	var denyDigests digestDenyFile
	if err := readJSON(filepath.Join(dir, "digest-deny.json"), &denyDigests); err != nil {
		return ciptypes.PolicyPack{}, err
	}
	var predicates predicatesFile
	if err := readJSON(filepath.Join(dir, "predicates.json"), &predicates); err != nil {
		return ciptypes.PolicyPack{}, err
	}
	var revocations revocationsFile
	if err := readJSON(filepath.Join(dir, "revocations.json"), &revocations); err != nil {
		return ciptypes.PolicyPack{}, err
	}

	return ciptypes.PolicyPack{
		Name:           name,
		BuilderDeny:    builders.Deny,
		BuilderRequire: builders.Require,
		DigestDenyPins: denyDigests.DenyDigests,
		PredicateAllow: predicates.Allow,
		Revocations:    revocations.Revocations,
	}, nil
}

func readJSON(path string, dst interface{}) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("read %s: %w", path, err)
	}
	if err := json.Unmarshal(b, dst); err != nil {
		return fmt.Errorf("parse %s: %w", path, err)
	}
	return nil
}
