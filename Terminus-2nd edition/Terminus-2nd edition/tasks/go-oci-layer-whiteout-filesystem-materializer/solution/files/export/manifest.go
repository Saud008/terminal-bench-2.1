package export

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/layerfuse/internal/ledgerio"
	"github.com/terminus/layerfuse/internal/types"
)

const DefaultOutputPath = "/app/output/filesystem-atlas.json"

// ManifestExport writes the filesystem manifest from the materialized stack.
func ManifestExport(stackPath, commitPath, outPath string) error {
	sf, err := ledgerio.LoadStack(stackPath)
	if err != nil {
		return err
	}
	commit, err := ledgerio.LoadCommit(commitPath)
	if err != nil {
		return err
	}
	entries := make([]types.ManifestEntry, 0, len(sf.Entries))
	for _, e := range sf.Entries {
		entries = append(entries, types.ManifestEntry{
			Path: e.Path,
			Type: e.Type,
			Mode: fmt.Sprintf("%04o", e.Mode&0o777),
			UID:  e.UID,
			GID:  e.GID,
		})
	}
	sort.Slice(entries, func(i, j int) bool { return entries[i].Path < entries[j].Path })
	hash := computeManifestHash(entries)
	doc := types.ManifestDoc{
		ManifestHash: hash,
		ReplaySeq:    commit.ReplaySeq,
		Entries:      entries,
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(outPath, data, 0o644)
}

func computeManifestHash(entries []types.ManifestEntry) string {
	lines := make([]string, 0, len(entries))
	for _, e := range entries {
		lines = append(lines, canonicalEntryLine(e))
	}
	payload := []byte(stringsJoin(lines, "\n"))
	sum := sha256.Sum256(payload)
	return hex.EncodeToString(sum[:])
}

func canonicalEntryLine(e types.ManifestEntry) string {
	obj := map[string]any{
		"gid":  e.GID,
		"mode": e.Mode,
		"path": e.Path,
		"type": string(e.Type),
		"uid":  e.UID,
	}
	data, _ := json.Marshal(obj)
	return string(data)
}

func stringsJoin(parts []string, sep string) string {
	if len(parts) == 0 {
		return ""
	}
	out := parts[0]
	for i := 1; i < len(parts); i++ {
		out += sep + parts[i]
	}
	return out
}
