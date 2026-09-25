package campaignio

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/airclos/internal/labtypes"
)

func LoadScenario(scenario, fixtureRoot string) ([]labtypes.NotamRecord, []labtypes.Sector, []labtypes.FlightPlan, []labtypes.Airway, []labtypes.FixPoint, labtypes.Policy, error) {
	base := filepath.Join(fixtureRoot, "scenarios", scenario)
	notams, err := readNotams(filepath.Join(base, "notams.jsonl"))
	if err != nil {
		return nil, nil, nil, nil, nil, labtypes.Policy{}, err
	}
	sort.Slice(notams, func(i, j int) bool {
		return notams[i].Amendment < notams[j].Amendment
	})
	sectors, err := readSectors(filepath.Join(base, "sectors.json"))
	if err != nil {
		return nil, nil, nil, nil, nil, labtypes.Policy{}, err
	}
	flights, err := readFlights(filepath.Join(base, "flights.jsonl"))
	if err != nil {
		return nil, nil, nil, nil, nil, labtypes.Policy{}, err
	}
	airways, err := readAirways(filepath.Join(base, "airways.json"))
	if err != nil {
		return nil, nil, nil, nil, nil, labtypes.Policy{}, err
	}
	fixes, err := readFixPoints(filepath.Join(base, "fix_points.json"))
	if err != nil {
		return nil, nil, nil, nil, nil, labtypes.Policy{}, err
	}
	policy, err := readPolicy(filepath.Join(base, "policy.json"))
	if err != nil {
		return nil, nil, nil, nil, nil, labtypes.Policy{}, err
	}
	return notams, sectors, flights, airways, fixes, policy, nil
}

func readNotams(path string) ([]labtypes.NotamRecord, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var out []labtypes.NotamRecord
	for _, line := range splitLines(string(raw)) {
		var rec labtypes.NotamRecord
		if err := json.Unmarshal([]byte(line), &rec); err != nil {
			return nil, err
		}
		out = append(out, rec)
	}
	return out, nil
}

func readSectors(path string) ([]labtypes.Sector, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var out []labtypes.Sector
	if err := json.Unmarshal(raw, &out); err != nil {
		return nil, err
	}
	return out, nil
}

func readFlights(path string) ([]labtypes.FlightPlan, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var out []labtypes.FlightPlan
	for _, line := range splitLines(string(raw)) {
		var fp labtypes.FlightPlan
		if err := json.Unmarshal([]byte(line), &fp); err != nil {
			return nil, err
		}
		out = append(out, fp)
	}
	return out, nil
}

func readFixPoints(path string) ([]labtypes.FixPoint, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var out []labtypes.FixPoint
	if err := json.Unmarshal(raw, &out); err != nil {
		return nil, err
	}
	return out, nil
}

func readAirways(path string) ([]labtypes.Airway, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var out []labtypes.Airway
	if err := json.Unmarshal(raw, &out); err != nil {
		return nil, err
	}
	return out, nil
}

func readPolicy(path string) (labtypes.Policy, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return labtypes.Policy{}, err
	}
	var p labtypes.Policy
	if err := json.Unmarshal(raw, &p); err != nil {
		return labtypes.Policy{}, err
	}
	return p, nil
}

func splitLines(s string) []string {
	var lines []string
	for _, line := range splitRaw(s) {
		if line != "" {
			lines = append(lines, line)
		}
	}
	return lines
}

func splitRaw(s string) []string {
	var out []string
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == '\n' {
			out = append(out, s[start:i])
			start = i + 1
		}
	}
	if start < len(s) {
		out = append(out, s[start:])
	}
	return out
}
