package staging

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"

	"github.com/chronostack/metricrollup/internal/model"
)

func WriteSnapshot(path string, snap model.RollupSnapshot) error {
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0644)
}

func WriteManifest(path string, stats model.IngestStats, snapshotPath string) error {
	snapBytes, err := os.ReadFile(snapshotPath)
	if err != nil {
		return err
	}
	sum := sha256.Sum256(snapBytes)
	manifest := model.ScrapeManifest{
		SchemaVersion:      1,
		ScrapesIngested:    stats.ScrapesIngested,
		LastScrapeTsMs:     0,
		SamplesAccepted:    stats.SamplesAccepted,
		CacheEntries:       stats.CacheEntries,
		RollupWindowsBuilt: stats.RollupWindows,
		StalenessMarkers:   stats.StalenessMarkers,
		ManifestSha256:     hex.EncodeToString(sum[:]),
	}
	raw, err := json.MarshalIndent(manifest, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0644)
}
