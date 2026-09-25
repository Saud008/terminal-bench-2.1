package verify

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/bundlectl/internal/bundle"
)

type SignatureEntry struct {
	KeyID     string `json:"key_id"`
	Scope     string `json:"scope"`
	ChainRoot string `json:"chain_root"`
	Signature string `json:"signature"`
}

type SignaturesFile struct {
	Signatures []SignatureEntry `json:"signatures"`
}

type KeysFile struct {
	Keys map[string]string `json:"keys"`
}

type Result struct {
	OK       bool              `json:"ok"`
	Revoked  bool              `json:"revoked,omitempty"`
	Reason   string            `json:"reason,omitempty"`
	ChainRoot string           `json:"chain_root,omitempty"`
	Digests  map[string]string `json:"digests,omitempty"`
}

func Run(bundleDir string) (*Result, error) {
	manifest, err := bundle.LoadManifest(bundleDir)
	if err != nil {
		return nil, err
	}
	members := make([]bundle.Member, 0)
	for _, raw := range manifest.Members {
		m, err := bundle.LoadMember(bundleDir, raw, nil)
		if err != nil {
			return &Result{OK: false, Reason: err.Error()}, nil
		}
		members = append(members, m)
	}
	sigRaw, err := os.ReadFile(filepath.Join(bundleDir, ".signatures.json"))
	if err != nil {
		return &Result{OK: false, Reason: err.Error()}, nil
	}
	var sf SignaturesFile
	if err := json.Unmarshal(sigRaw, &sf); err != nil {
		return nil, err
	}
	for _, ent := range sf.Signatures {
		rev, err := IsRevoked(bundleDir, ent.KeyID)
		if err != nil {
			return nil, err
		}
		if rev {
			return &Result{OK: false, Revoked: true, Reason: "revoked key"}, nil
		}
	}
	chainMembers := make([]bundle.Member, 0)
	for _, m := range members {
		if m.Canonical != "MANIFEST.json" && m.Canonical != ".signatures.json" {
			chainMembers = append(chainMembers, m)
		}
	}
	if err := bundle.IngestPreview(bundleDir, chainMembers, manifest.Members); err != nil {
		return nil, err
	}
	root, digests := ChainRoot(chainMembers, manifest.Members)
	for _, ent := range sf.Signatures {
		scoped := ScopedChainRoot(members, ent.Scope, manifest.Members)
		if scoped != ent.ChainRoot {
			return &Result{OK: false, Reason: fmt.Sprintf("scope %s chain mismatch", ent.Scope)}, nil
		}
		if err := checkMAC(bundleDir, ent); err != nil {
			return &Result{OK: false, Reason: err.Error()}, nil
		}
	}
	ordered := make([]string, 0, len(digests))
	for k := range digests {
		ordered = append(ordered, k)
	}
	sort.Strings(ordered)
	outDigests := make(map[string]string, len(ordered))
	for _, k := range ordered {
		outDigests[k] = digests[k]
	}
	return &Result{OK: true, ChainRoot: root, Digests: outDigests}, nil
}

func checkMAC(bundleDir string, ent SignatureEntry) error {
	raw, err := os.ReadFile(filepath.Join(bundleDir, "..", "..", "trust", "keys.json"))
	if err != nil {
		raw, err = os.ReadFile("/app/trust/keys.json")
		if err != nil {
			return err
		}
	}
	var kf KeysFile
	if err := json.Unmarshal(raw, &kf); err != nil {
		return err
	}
	mat, ok := kf.Keys[ent.KeyID]
	if !ok {
		return fmt.Errorf("unknown key %s", ent.KeyID)
	}
	mac := hmac.New(sha256.New, []byte(mat))
	mac.Write([]byte(ent.Scope))
	mac.Write([]byte(ent.ChainRoot))
	expect := hex.EncodeToString(mac.Sum(nil))
	if expect != ent.Signature {
		return fmt.Errorf("bad signature for %s", ent.KeyID)
	}
	return nil
}
