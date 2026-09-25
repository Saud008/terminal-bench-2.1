package digest

import (
	"crypto/sha256"
	"encoding/hex"
	"path/filepath"
	"sort"
	"strings"

	"github.com/terminus/mlflow-provenance-curator/internal/model"
)

func normalizeRel(path string) string {
	p := strings.TrimPrefix(path, "./")
	return filepath.ToSlash(filepath.Clean(p))
}

func DigestArtifact(relPath, content string) string {
	rel := normalizeRel(relPath)
	payload := rel + "\n" + content
	sum := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(sum[:])
}

func CollectFocusArtifacts(run model.ScopedRun) []model.ArtifactDigest {
	out := make([]model.ArtifactDigest, 0, len(run.Artifacts))
	for _, a := range run.Artifacts {
		rel := normalizeRel(a.RelPath)
		out = append(out, model.ArtifactDigest{
			RelPath: rel,
			Digest:  DigestArtifact(a.RelPath, a.Content),
		})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].RelPath < out[j].RelPath })
	return out
}
