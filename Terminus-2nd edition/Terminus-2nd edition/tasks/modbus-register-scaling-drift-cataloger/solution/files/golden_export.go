package export

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/modbus-drift-cataloger/internal/catalog"
	"github.com/terminus/modbus-drift-cataloger/internal/ingest"
	"github.com/terminus/modbus-drift-cataloger/internal/model"
)

func catalogDigest(body map[string]any) string {
	delete(body, "catalog_digest")
	keys := make([]string, 0, len(body))
	for k := range body {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	var buf bytes.Buffer
	buf.WriteByte('{')
	for i, k := range keys {
		if i > 0 {
			buf.WriteByte(',')
		}
		kb, _ := json.Marshal(k)
		buf.Write(kb)
		buf.WriteByte(':')
		vb, _ := json.Marshal(body[k])
		buf.Write(vb)
	}
	buf.WriteByte('}')
	sum := sha256.Sum256(buf.Bytes())
	return hex.EncodeToString(sum[:])
}

func BuildDriftCatalog(gen model.CatalogGeneration) model.DriftCatalog {
	out := model.DriftCatalog{
		CatalogGeneration: gen.Generation,
		StagingGeneration: gen.StagingGeneration,
		Entries:           gen.Entries,
	}
	raw, _ := json.Marshal(out)
	var m map[string]any
	_ = json.Unmarshal(raw, &m)
	out.CatalogDigest = catalogDigest(m)
	return out
}

func WriteDriftCatalog(path string, cat model.DriftCatalog) error {
	raw, err := json.MarshalIndent(cat, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}

func RunExport(snap model.PollStaging, genPath, outPath string) error {
	gen, err := catalog.ReadGeneration(genPath)
	if err != nil {
		return err
	}
	if gen.Generation < 1 {
		return fmt.Errorf("catalog_generation must be > 0")
	}
	want := ingest.ComputeFramesDigest(snap.Frames)
	if snap.FramesDigest != want {
		return fmt.Errorf("frames_digest mismatch")
	}
	if gen.StagingGeneration != snap.StagingGeneration {
		return fmt.Errorf("staging_generation mismatch")
	}
	drift := BuildDriftCatalog(gen)
	return WriteDriftCatalog(outPath, drift)
}
