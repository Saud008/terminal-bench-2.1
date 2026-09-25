package rosterfreeze

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/formulatrix/internal/model"
	"github.com/terminus/formulatrix/internal/formndc"
)

const DefaultRosterPath = "/app/state/formulary-roster.json"

type rosterDigestPayload struct {
	AsOf       string             `json:"as_of"`
	Drugs      []model.Drug       `json:"drugs"`
	Overrides  []model.Override   `json:"overrides"`
	Plans      []model.Plan       `json:"plans"`
	Scenario   string             `json:"scenario"`
	StepChains []model.StepLink  `json:"step_chains"`
}

func WriteRoster(path string, snap model.RosterFile) error {
	if path == "" {
		path = DefaultRosterPath
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	digest, err := computeDigest(snap)
	if err != nil {
		return err
	}
	snap.RosterDigest = digest
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func ReadRoster(path string) (model.RosterFile, error) {
	if path == "" {
		path = DefaultRosterPath
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.RosterFile{}, err
	}
	var snap model.RosterFile
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.RosterFile{}, err
	}
	return snap, nil
}

func computeDigest(snap model.RosterFile) (string, error) {
	drugs := make([]model.Drug, len(snap.Drugs))
	copy(drugs, snap.Drugs)
	sort.Slice(drugs, func(i, j int) bool {
		return formndc.NormalizeNDC(drugs[i].NDC) < formndc.NormalizeNDC(drugs[j].NDC)
	})
	payload := rosterDigestPayload{
		AsOf:       snap.AsOf,
		Drugs:      drugs,
		Overrides:  snap.Overrides,
		Plans:      snap.Plans,
		Scenario:   snap.Scenario,
		StepChains: snap.StepChains,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}
