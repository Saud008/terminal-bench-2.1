package bindvault

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/airclos/internal/labtypes"
)

const DefaultBindingPath = "/app/state/campaign-binding.json"

func WriteBinding(path string, binding labtypes.CampaignBinding) error {
	if path == "" {
		path = DefaultBindingPath
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	digest, err := computeDigest(binding.Scenario, binding.Notams, binding.Sectors, binding.Flights, binding.Airways)
	if err != nil {
		return err
	}
	binding.BindingDigest = digest
	data, err := json.MarshalIndent(binding, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func ReadBinding(path string) (labtypes.CampaignBinding, error) {
	if path == "" {
		path = DefaultBindingPath
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return labtypes.CampaignBinding{}, err
	}
	var binding labtypes.CampaignBinding
	if err := json.Unmarshal(raw, &binding); err != nil {
		return labtypes.CampaignBinding{}, err
	}
	return binding, nil
}

func computeDigest(scenario string, notams []labtypes.NotamRecord, sectors []labtypes.Sector, flights []labtypes.FlightPlan, airways []labtypes.Airway) (string, error) {
	payload := map[string]any{
		"scenario": scenario,
		"notams":   notams,
		"sectors":  sectors,
		"flights":  flights,
		"airways":  airways,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}
