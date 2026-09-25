package ingest

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"sort"

	"yaracor/internal/policy"
	"yaracor/internal/model"
	"yaracor/internal/staging"
)

func ComputeEventsDigest(events []model.ScanEvent) string {
	ordered := append([]model.ScanEvent(nil), events...)
	sort.Slice(ordered, func(i, j int) bool {
		if ordered[i].DetectedMs == ordered[j].DetectedMs {
			return ordered[i].EventID < ordered[j].EventID
		}
		return ordered[i].DetectedMs < ordered[j].DetectedMs
	})
	body := ""
	for _, ev := range ordered {
		raw, _ := json.Marshal(ev)
		body += string(raw) + "\n"
	}
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
}

func WriteStaging(stagingPath, seqPath, policyPath string, events []model.ScanEvent) error {
	phash, err := policy.SHA256File(policyPath)
	if err != nil {
		return err
	}
	gen, err := staging.BumpSeq(seqPath)
	if err != nil {
		return err
	}
	snap := model.EventStaging{
		Events:            events,
		EventsDigest:      ComputeEventsDigest(events),
		PolicySHA256:      phash,
		PolicyPath:        policyPath,
		StagingGeneration: gen,
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(stagingPath, raw, 0o644)
}
