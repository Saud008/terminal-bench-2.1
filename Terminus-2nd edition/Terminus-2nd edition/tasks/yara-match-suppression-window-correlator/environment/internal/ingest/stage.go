package ingest

import (
	"encoding/json"
	"os"
	"sort"

	"yaracor/internal/model"
	"yaracor/internal/policy"
	"yaracor/internal/staging"
)

func ComputeEventsDigest(events []model.ScanEvent) string {
	ordered := append([]model.ScanEvent(nil), events...)
	sort.Slice(ordered, func(i, j int) bool {
		return ordered[i].EventID < ordered[j].EventID
	})
	h := uint64(1469598103934665603)
	for _, ev := range ordered {
		raw, _ := json.Marshal(ev)
		for _, b := range raw {
			h ^= uint64(b)
			h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
		}
	}
	return sprintf16(h)
}

func sprintf16(h uint64) string {
	const hexdigits = "0123456789abcdef"
	out := make([]byte, 16)
	for i := 15; i >= 0; i-- {
		out[i] = hexdigits[h&0xF]
		h >>= 4
	}
	return string(out)
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
