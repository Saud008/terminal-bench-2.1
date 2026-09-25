package matrixout

// Case-6 export stage for formulatrix: publish-matrix seals the matrix report.

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/formulatrix/internal/model"
	"github.com/terminus/formulatrix/internal/rosterfreeze"
	"github.com/terminus/formulatrix/internal/store"
)

const (
	defaultOut = "/app/output/formulary-matrix.json"
	genPath    = "/app/state/refresh-revision.json"
)

type reportDigestPayload struct {
	AsOf     string            `json:"as_of"`
	RowCount int               `json:"row_count"`
	Rows     []model.MatrixRow `json:"rows"`
	Scenario string            `json:"scenario"`
}

func Emit(scenario, outPath string) error {
	var gen model.RevisionFile
	raw, err := os.ReadFile(genPath)
	if err != nil {
		return fmt.Errorf("refresh_revision missing")
	}
	if err := json.Unmarshal(raw, &gen); err != nil {
		return err
	}
	if gen.RefreshRevision <= 0 {
		return fmt.Errorf("publish blocked: refresh_revision must be > 0")
	}
	stage, err := rosterfreeze.ReadRoster("")
	if err != nil {
		return err
	}
	db, err := store.Open("")
	if err != nil {
		return err
	}
	defer db.Close()
	rows, err := store.ReadRows(db)
	if err != nil {
		return err
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].PlanID != rows[j].PlanID {
			return rows[i].PlanID < rows[j].PlanID
		}
		return rows[i].NDCNormalized < rows[j].NDCNormalized
	})
	publish := model.MatrixReport{
		Scenario: scenario,
		AsOf:     stage.AsOf,
		RowCount: len(rows),
		Rows:     rows,
	}
	digest, err := reportDigest(publish)
	if err != nil {
		return err
	}
	publish.MatrixDigest = digest
	if outPath == "" {
		outPath = defaultOut
	}
	return writeReport(outPath, publish)
}

func reportDigest(exp model.MatrixReport) (string, error) {
	payload := reportDigestPayload{
		AsOf:     exp.AsOf,
		RowCount: exp.RowCount,
		Rows:     exp.Rows,
		Scenario: exp.Scenario,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}

func writeReport(path string, exp model.MatrixReport) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(exp, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}
