package export

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"

	"github.com/terminus/lokilogql/internal/staging"
	"github.com/terminus/lokilogql/internal/types"
)

const DefaultFingerprintPath = "/app/output/query-fingerprint.json"

// BuildFingerprint reads stage state and writes query fingerprint export.
func BuildFingerprint(stagePath, outPath string, exportPass int) error {
	st, err := staging.Load(stagePath)
	if err != nil {
		return err
	}
	sum := uint64(0)
	for _, v := range st.Vectors {
		sum += v.Checksum
	}
	fp := sha256.Sum256([]byte(st.Query.Raw))
	out := types.FingerprintFile{
		Fingerprint:    hex.EncodeToString(fp[:]),
		SelectedLabels: st.SelectedGroupLabels,
		VectorChecksum: sum,
		ExportPass:     exportPass,
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(outPath, data, 0o644)
}
