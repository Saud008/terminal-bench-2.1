// Package jktpin owns the session-open path: verifying the initial DPoP
// proof, checking the presented jwk's thumbprint against the pin registry,
// minting the vault HMAC bind ticket, and creating the session record. See
// /app/docs/vault-hmac-bind.md and /app/docs/dpop-http-routes.md.
package jktpin

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/jktadmit-gate/internal/hmacbind"
	"github.com/terminus/jktadmit-gate/internal/proofparse"
	"github.com/terminus/jktadmit-gate/internal/schema"
	"github.com/terminus/jktadmit-gate/internal/sessionstore"
)

// Registry is the jkt pin allow-list loaded from <pin dir>/jkt_pins.json.
// mode "allow_all" accepts any jkt; mode "allowlist" requires the computed
// jkt to appear in jkts.
type Registry struct {
	Mode string   `json:"mode"`
	JKTs []string `json:"jkts"`
}

type Manager struct {
	Store      *sessionstore.Store
	VaultKey   []byte
	PinDir     string
	OpenHTU    string
	IatSkewSec int64
}

const pinDirEnv = "JKTADMIT_PIN_DIR"

// resolvePinDir honors JKTADMIT_PIN_DIR over the configured default, per
// /app/docs/vault-hmac-bind.md.
func (m *Manager) resolvePinDir() string {
	if v := os.Getenv(pinDirEnv); v != "" {
		return v
	}
	return m.PinDir
}

// LoadRegistry resolves the pin registry directory and reads
// jkt_pins.json from it, defaulting to allow_all when the file is absent.
func (m *Manager) LoadRegistry() (Registry, error) {
	dir := m.resolvePinDir()
	raw, err := os.ReadFile(filepath.Join(dir, "jkt_pins.json"))
	if err != nil {
		return Registry{Mode: "allow_all"}, nil
	}
	var reg Registry
	if err := json.Unmarshal(raw, &reg); err != nil {
		return Registry{}, fmt.Errorf("malformed pin registry: %w", err)
	}
	return reg, nil
}

func containsJKT(list []string, jkt string) bool {
	for _, v := range list {
		if v == jkt {
			return true
		}
	}
	return false
}

// Open verifies the initial proof, resolves the jkt pin, checks the
// registry, mints the bind ticket, and stores the new session.
func (m *Manager) Open(req schema.OpenRequest, nowUnix int64) (bindTicket string, jkt string, err error) {
	proof, err := proofparse.Parse(req.DPoPProof)
	if err != nil {
		return "", "", fmt.Errorf("malformed proof: %w", err)
	}
	if !proofparse.CheckAlg(proof.Header.Alg) {
		return "", "", fmt.Errorf("alg_rejected")
	}
	if err := proofparse.VerifySignature(proof); err != nil {
		return "", "", fmt.Errorf("bad_signature: %w", err)
	}
	if !proofparse.CheckHTM(proof.Payload.Htm, "POST") {
		return "", "", fmt.Errorf("htm_mismatch")
	}
	if !proofparse.CheckHTU(proof.Payload.Htu, m.OpenHTU) {
		return "", "", fmt.Errorf("htu_mismatch")
	}
	if !proofparse.CheckIat(proof.Payload.Iat, nowUnix, m.IatSkewSec) {
		return "", "", fmt.Errorf("iat_skew")
	}

	jkt = proofparse.Thumbprint(proof.Header.JWK)

	reg, err := m.LoadRegistry()
	if err != nil {
		return "", "", err
	}
	if reg.Mode == "allowlist" && !containsJKT(reg.JKTs, jkt) {
		return "", "", fmt.Errorf("jkt_not_registered")
	}

	tix := hmacbind.Mint(m.VaultKey, req.Principal, req.Session, jkt)
	sess := schema.SessionState{
		Principal:  req.Principal,
		Session:    req.Session,
		JKT:        jkt,
		BindTicket: tix,
		DenyTotals: schema.NewDenyTotals(),
	}
	m.Store.Put(sessionstore.Key(req.Principal, req.Session), sess)
	return tix, jkt, nil
}
