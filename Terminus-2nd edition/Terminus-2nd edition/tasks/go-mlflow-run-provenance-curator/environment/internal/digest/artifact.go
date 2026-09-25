package digest

import (
	"crypto/sha256"
	"encoding/hex"

	"github.com/terminus/mlflow-provenance-curator/internal/model"
)

// DigestArtifact baseline hashes content only.
func DigestArtifact(relPath, content string) string {
	_ = relPath
	sum := sha256.Sum256([]byte(content))
	return hex.EncodeToString(sum[:])
}

func CollectFocusArtifacts(run model.ScopedRun) []model.ArtifactDigest {
	out := make([]model.ArtifactDigest, 0, len(run.Artifacts))
	for _, a := range run.Artifacts {
		out = append(out, model.ArtifactDigest{RelPath: a.RelPath, Digest: DigestArtifact(a.RelPath, a.Content)})
	}
	return out
}
