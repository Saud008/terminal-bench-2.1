package planemit

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/iceexpctl/internal/branchtag"
	"github.com/terminus/iceexpctl/internal/deletefile"
	"github.com/terminus/iceexpctl/internal/manifestreach"
	"github.com/terminus/iceexpctl/internal/model"
	"github.com/terminus/iceexpctl/internal/orphan"
	"github.com/terminus/iceexpctl/internal/snapgraph"
	"github.com/terminus/iceexpctl/internal/cursorsnap"
)

const (
	defaultPlan   = "/app/output/expiry-plan.json"
	defaultOrphan = "/app/output/orphan-ledger.jsonl"
	genPath       = "/app/state/analyze-revision.json"
)

func Emit(scenario, planPath, orphanPath string) error {
	var gen model.RevisionFile
	raw, err := os.ReadFile(genPath)
	if err != nil {
		return fmt.Errorf("analyze_revision missing")
	}
	if err := json.Unmarshal(raw, &gen); err != nil {
		return err
	}
	if gen.AnalyzeRevision <= 0 {
		return fmt.Errorf("emit blocked: analyze_revision must be > 0")
	}
	stage, err := cursorsnap.ReadStage("")
	if err != nil {
		return err
	}
	plan, orphans := buildPlan(stage, scenario)
	if planPath == "" {
		planPath = defaultPlan
	}
	if orphanPath == "" {
		orphanPath = defaultOrphan
	}
	if err := writePlan(planPath, plan); err != nil {
		return err
	}
	return writeOrphans(orphanPath, orphans)
}

func buildPlan(stage model.CursorSnapshot, scenario string) (model.ExpiryPlan, []model.OrphanRow) {
	protected := branchtag.ProtectedSet(stage.Table)
	current, _ := snapgraph.SnapshotByID(stage.Table, stage.Table.CurrentSnapshotID)
	retention := deletefile.RetentionHours(stage.Table.DeleteRetentionHours)
	expired := make([]int64, 0)
	for _, snap := range stage.Table.Snapshots {
		if protected[snap.SnapshotID] {
			continue
		}
		if deletefile.DeleteEligible(snap.EventMs, current.EventMs, retention) {
			expired = append(expired, snap.SnapshotID)
		}
	}
	sort.Slice(expired, func(i, j int) bool { return expired[i] < expired[j] })
	root := current.ManifestList
	live := manifestreach.ReachableFiles(stage.Manifests, root)
	orphans := orphan.OrphanPaths(stage.Manifests, live)
	plan := model.ExpiryPlan{
		Scenario:           scenario,
		ProtectedCount:     len(protected),
		ExpiredSnapshotIDs: expired,
	}
	digest, _ := planDigest(plan)
	plan.PlanDigest = digest
	return plan, orphans
}

func planDigest(plan model.ExpiryPlan) (string, error) {
	payload := map[string]any{
		"expired_snapshot_ids": plan.ExpiredSnapshotIDs,
		"protected_count":      plan.ProtectedCount,
		"scenario":             plan.Scenario,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}

func writePlan(path string, plan model.ExpiryPlan) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(plan, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func writeOrphans(path string, rows []model.OrphanRow) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	var buf []byte
	for _, row := range rows {
		line, err := json.Marshal(row)
		if err != nil {
			return err
		}
		buf = append(buf, line...)
		buf = append(buf, '\n')
	}
	return os.WriteFile(path, buf, 0o644)
}
