package ingest

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/terminus/nfresume/internal/digest"
	"github.com/terminus/nfresume/internal/globexpand"
	"github.com/terminus/nfresume/internal/lineage"
	"github.com/terminus/nfresume/internal/model"
	"github.com/terminus/nfresume/internal/staging"
)

func Run(seed, scenarioID, fixtureRoot string) error {
	root := fixtureRoot
	if root == "" {
		root = "/app/fixtures"
	}
	manifestPath := filepath.Join(root, "scenarios", scenarioID+".json")
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return err
	}
	var manifest model.ScenarioFile
	if err := json.Unmarshal(data, &manifest); err != nil {
		return err
	}
	runDir := filepath.Join(root, manifest.RunDir)
	metaPath := filepath.Join(runDir, "run.meta.json")
	metaData, err := os.ReadFile(metaPath)
	if err != nil {
		return err
	}
	var meta model.RunMeta
	if err := json.Unmarshal(metaData, &meta); err != nil {
		return err
	}

	traceDir := filepath.Join(runDir, "trace")
	entries, err := os.ReadDir(traceDir)
	if err != nil {
		return err
	}
	var traceFiles []string
	for _, e := range entries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".json") {
			traceFiles = append(traceFiles, e.Name())
		}
	}
	sort.Strings(traceFiles)

	hasher := sha256.New()
	hasher.Write([]byte(meta.RunID))
	var staged []model.StagedTask
	for _, name := range traceFiles {
		raw, err := os.ReadFile(filepath.Join(traceDir, name))
		if err != nil {
			return err
		}
		var rec model.TaskRecord
		if err := json.Unmarshal(raw, &rec); err != nil {
			return fmt.Errorf("%s: %w", name, err)
		}
		hasher.Write([]byte(rec.TaskID))

		containerDigest := digest.NormalizeDigest(rec.ContainerDigest)
		expandHash := computeExpansionHash(runDir, rec.InputGlobs)
		lineageDigest := lineage.ComputeLineageDigest(rec.ParentHashes, rec.Hash)
		if strings.TrimSpace(rec.LineageDigest) != "" {
			lineageDigest = strings.TrimSpace(rec.LineageDigest)
		}

		cacheSession := ""
		markerPath := filepath.Join(runDir, "work", sanitizeTaskID(rec.TaskID), ".nf_cached.json")
		if b, err := os.ReadFile(markerPath); err == nil {
			var marker model.CacheMarker
			if json.Unmarshal(b, &marker) == nil {
				cacheSession = marker.SessionID
			}
		}

		staged = append(staged, model.StagedTask{
			TaskID:          rec.TaskID,
			Hash:            rec.Hash,
			LineageDigest:   lineageDigest,
			ParentHashes:    rec.ParentHashes,
			ContainerDigest: containerDigest,
			ExpansionHash:   rec.ExpansionHash,
			ComputedExpand:  expandHash,
			Attempt:         rec.Attempt,
			Cached:          rec.Cached,
			ExitStatus:      rec.ExitStatus,
			PriorDigest:     digest.NormalizeDigest(rec.PriorDigest),
			PriorExitStatus: rec.PriorExitStatus,
			CacheSessionID:  cacheSession,
		})
	}

	snap := model.StageSnapshot{
		Engine:    "nfresume-v1",
		Scenario:  scenarioID,
		RunID:     meta.RunID,
		SessionID: meta.SessionID,
		Resumed:   meta.Resumed,
		TaskCount: len(staged),
		Tasks:     staged,
		AuditGen:  0,
		RunDigest: hex.EncodeToString(hasher.Sum(nil)),
	}
	return staging.WriteStage(staging.DefaultStagePath, snap)
}

func computeExpansionHash(runDir string, globs []string) string {
	h := sha256.New()
	var all []string
	for _, g := range globs {
		paths, err := globexpand.ExpandSorted(runDir, g)
		if err != nil {
			continue
		}
		all = append(all, paths...)
	}
	sort.Strings(all)
	for _, p := range all {
		h.Write([]byte(p))
		h.Write([]byte{0})
	}
	return hex.EncodeToString(h.Sum(nil))
}

func sanitizeTaskID(id string) string {
	return strings.ReplaceAll(id, ":", "_")
}
