package ingest

import (
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/modbus-drift-cataloger/internal/manifest"
	"github.com/terminus/modbus-drift-cataloger/internal/model"
	"github.com/terminus/modbus-drift-cataloger/internal/staging"
)

// Broken: FNV-style digest instead of sha256 canonical lines per poll-staging.md.
func ComputeFramesDigest(frames []model.Frame) string {
	ordered := append([]model.Frame(nil), frames...)
	sort.Slice(ordered, func(i, j int) bool {
		return ordered[i].FrameID < ordered[j].FrameID
	})
	h := uint64(1469598103934665603)
	for _, fr := range ordered {
		raw, _ := json.Marshal(fr)
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

func WriteStaging(stagingPath, seqPath, manifestPath string, frames []model.Frame) error {
	mhash, err := manifest.SHA256File(manifestPath)
	if err != nil {
		return err
	}
	gen, err := staging.BumpSeq(seqPath)
	if err != nil {
		return err
	}
	snap := model.PollStaging{
		Frames:            frames,
		FramesDigest:      ComputeFramesDigest(frames),
		ManifestSHA256:    mhash,
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
