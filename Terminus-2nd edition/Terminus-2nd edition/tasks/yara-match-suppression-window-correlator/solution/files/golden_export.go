package export

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"yaracor/internal/correlate"
	"yaracor/internal/ingest"
	"yaracor/internal/model"
)

func BuildBundle(gen model.CorrelateGeneration) model.IncidentBundle {
	bundle := model.IncidentBundle{
		CorrelateGeneration: gen.Generation,
		StagingGeneration:   gen.StagingGeneration,
		Incidents:           gen.Incidents,
	}
	bundle.BundleDigest = computeBundleDigest(bundle)
	return bundle
}

func computeBundleDigest(bundle model.IncidentBundle) string {
	incRaw, _ := json.Marshal(bundle.Incidents)
	var incidents []any
	_ = json.Unmarshal(incRaw, &incidents)
	payload := map[string]any{
		"correlate_generation": bundle.CorrelateGeneration,
		"staging_generation":   bundle.StagingGeneration,
		"incidents":            incidents,
	}
	raw, _ := json.Marshal(normalize(payload))
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}

func normalize(v any) any {
	switch t := v.(type) {
	case map[string]any:
		keys := make([]string, 0, len(t))
		for k := range t {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		out := make(map[string]any, len(t))
		for _, k := range keys {
			out[k] = normalize(t[k])
		}
		return out
	case []any:
		out := make([]any, len(t))
		for i, item := range t {
			out[i] = normalize(item)
		}
		return out
	case float64:
		if t == float64(int64(t)) {
			return int64(t)
		}
		return t
	default:
		return v
	}
}

func WriteBundle(path string, bundle model.IncidentBundle) error {
	raw, err := json.MarshalIndent(bundle, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}

func RunExport(snap model.EventStaging, genPath, outPath string) error {
	gen, err := correlate.ReadGeneration(genPath)
	if err != nil {
		return err
	}
	if gen.Generation < 1 {
		return fmt.Errorf("correlate_generation zero")
	}
	expected := ingest.ComputeEventsDigest(snap.Events)
	if expected != snap.EventsDigest {
		return fmt.Errorf("events_digest mismatch")
	}
	bundle := BuildBundle(gen)
	return WriteBundle(outPath, bundle)
}
