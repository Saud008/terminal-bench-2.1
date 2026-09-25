package sarif

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/sarbctl-curator/internal/model"
)

type sarifDoc struct {
	Runs []struct {
		Tool struct {
			Driver struct {
				Name string `json:"name"`
			} `json:"driver"`
		} `json:"tool"`
		Results []struct {
			RuleID               string            `json:"ruleId"`
			Level                string            `json:"level"`
			Message              struct{ Text string } `json:"message"`
			Locations            []struct {
				PhysicalLocation struct {
					ArtifactLocation struct{ URI string } `json:"artifactLocation"`
					Region           struct {
						StartLine   int `json:"startLine"`
						StartColumn int `json:"startColumn"`
					} `json:"region"`
				} `json:"physicalLocation"`
			} `json:"locations"`
			PartialFingerprints map[string]string `json:"partialFingerprints"`
			Properties          map[string]any    `json:"properties"`
		} `json:"results"`
	} `json:"runs"`
}

func SHA256File(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return SHA256Bytes(raw), nil
}

func LoadFindings(path string) ([]model.Finding, string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, "", err
	}
	var doc sarifDoc
	if err := json.Unmarshal(raw, &doc); err != nil {
		return nil, "", err
	}
	if len(doc.Runs) == 0 {
		return nil, "", fmt.Errorf("no sarif runs")
	}
	run := doc.Runs[0]
	tool := run.Tool.Driver.Name
	var out []model.Finding
	for _, r := range run.Results {
		if len(r.Locations) == 0 {
			continue
		}
		loc := r.Locations[0].PhysicalLocation
		props := r.Properties
		fid, _ := props["finding_id"].(string)
		obs, _ := props["observed_at"].(string)
		fp := r.PartialFingerprints["primaryLocationLineHash"]
		out = append(out, model.Finding{
			FindingID:   fid,
			Tool:        tool,
			RuleID:      r.RuleID,
			Level:       r.Level,
			Message:     r.Message.Text,
			URI:         loc.ArtifactLocation.URI,
			StartLine:   loc.Region.StartLine,
			StartColumn: loc.Region.StartColumn,
			Fingerprint: fp,
			ObservedAt:  obs,
		})
	}
	return out, tool, nil
}

func LoadBaseline(path string) (model.BaselineSnapshot, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.BaselineSnapshot{}, err
	}
	var snap model.BaselineSnapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.BaselineSnapshot{}, err
	}
	return snap, nil
}
