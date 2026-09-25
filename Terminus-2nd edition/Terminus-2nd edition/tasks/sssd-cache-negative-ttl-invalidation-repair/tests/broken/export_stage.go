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
	active := append([]model.NegativeExport(nil), snap.Negatives...)
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
