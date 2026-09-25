package export

import (
	"encoding/json"
	"os"

	"github.com/terminus/sssdcache/internal/model"
	"github.com/terminus/sssdcache/internal/staging"
)

func Publish(snapshotPath, outPath string) error {
	snap, err := staging.Read(snapshotPath)
	if err != nil {
		return err
	}
	active := filterActiveNegatives(snap.Negatives, snap.EvaluatedAtMS)
	doc := model.CacheReport{
		DomainSuffix:    snap.DomainSuffix,
		ActiveNegatives: active,
		Positives:       snap.Positives,
		Stats:           snap.Stats,
	}
	raw, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile(outPath, raw, 0o644)
}

func filterActiveNegatives(negatives []model.NegativeExport, evaluatedAtMS int64) []model.NegativeExport {
	out := make([]model.NegativeExport, 0, len(negatives))
	for _, n := range negatives {
		if n.ExpiresAt > evaluatedAtMS {
			out = append(out, n)
		}
	}
	return out
}
