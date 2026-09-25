package ingest

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/modbus-drift-cataloger/internal/manifest"
	"github.com/terminus/modbus-drift-cataloger/internal/model"
	"github.com/terminus/modbus-drift-cataloger/internal/staging"
)

func ComputeFramesDigest(frames []model.Frame) string {
	ordered := append([]model.Frame(nil), frames...)
	sort.Slice(ordered, func(i, j int) bool {
		if ordered[i].ReceivedMs == ordered[j].ReceivedMs {
			return ordered[i].FrameID < ordered[j].FrameID
		}
		return ordered[i].ReceivedMs < ordered[j].ReceivedMs
	})
	body := ""
	for i, fr := range ordered {
		raw, _ := json.Marshal(fr)
		body += string(raw)
		if i < len(ordered)-1 {
			body += "\n"
		}
	}
	if len(ordered) > 0 {
		body += "\n"
	}
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
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
		ManifestPath:      manifestPath,
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
