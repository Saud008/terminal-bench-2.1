package ingest

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"github.com/terminus/brat-consensus-exporter/internal/model"
	"github.com/terminus/brat-consensus-exporter/internal/revision"
)

func LoadProject(dir string) (model.Project, error) {
	raw, err := os.ReadFile(filepath.Join(dir, "project.json"))
	if err != nil {
		return model.Project{}, err
	}
	var p model.Project
	if err := json.Unmarshal(raw, &p); err != nil {
		return model.Project{}, err
	}
	return p, nil
}

func LoadAnnotations(dir string, annotators []model.Annotator) ([]model.AnnotationFile, error) {
	annDir := filepath.Join(dir, "annotations")
	entries, err := os.ReadDir(annDir)
	if err != nil {
		return nil, err
	}
	var out []model.AnnotationFile
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".json") {
			continue
		}
		raw, err := os.ReadFile(filepath.Join(annDir, e.Name()))
		if err != nil {
			return nil, err
		}
		var f model.AnnotationFile
		if err := json.Unmarshal(raw, &f); err != nil {
			return nil, err
		}
		out = append(out, f)
	}
	return out, nil
}

func ProjectDigest(dir string) (string, error) {
	h := sha256.New()
	err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return err
		}
		if strings.HasSuffix(path, ".json") {
			b, rerr := os.ReadFile(path)
			if rerr != nil {
				return rerr
			}
			h.Write([]byte(path))
			h.Write(b)
		}
		return nil
	})
	if err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

func StageAnnotations(project model.Project, files []model.AnnotationFile) (model.AnnotationStaging, error) {
	weights := map[string]float64{}
	adj := map[string]bool{}
	for _, a := range project.Annotators {
		weights[a.ID] = a.Weight
		adj[a.ID] = a.Adjudicator
	}
	spans := make([]model.StagedSpan, 0)
	relations := make([]model.StagedRelation, 0)
	for _, f := range files {
		w := weights[f.Annotator]
		canLock := adj[f.Annotator]
		for _, s := range f.Spans {
			locked := false
			if canLock {
				for _, lk := range f.Locks {
					if lk.Kind == "span" && lk.DocID == s.DocID && lk.SpanID == s.ID {
						locked = true
					}
				}
			}
			row := model.StagedSpan{
				SourceID: s.ID, Annotator: f.Annotator, DocID: s.DocID, Revision: s.Revision,
				Start: s.Start, End: s.End, Label: s.Label, Weight: w, Locked: locked,
			}
			spans = append(spans, revision.NormalizeSpan(project, row))
		}
		for _, r := range f.Relations {
			locked := false
			if canLock {
				for _, lk := range f.Locks {
					if lk.Kind == "relation" && lk.DocID == r.DocID && lk.RelID == r.ID {
						locked = true
					}
				}
			}
			relations = append(relations, model.StagedRelation{
				SourceID: r.ID, Annotator: f.Annotator, DocID: r.DocID,
				From: r.From, To: r.To, Type: r.Type, Weight: w, Locked: locked,
			})
		}
	}
	return model.AnnotationStaging{
		ProjectID: project.ProjectID,
		Project:   project,
		Spans:     spans,
		Relations: relations,
	}, nil
}

func WriteStaging(stagePath, seqPath, projectPath string, stage model.AnnotationStaging) error {
	prev := 0
	if b, err := os.ReadFile(seqPath); err == nil {
		var seq model.StagingSeq
		if json.Unmarshal(b, &seq) == nil {
			prev = seq.StagingGeneration
		}
	}
	stage.StagingGeneration = prev + 1
	stage.ProjectPath = projectPath
	digest, err := ProjectDigest(projectPath)
	if err != nil {
		return err
	}
	stage.ProjectDigest = digest
	if err := os.MkdirAll(filepath.Dir(stagePath), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(stage, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(stagePath, append(raw, '\n'), 0o644); err != nil {
		return err
	}
	seqRaw, _ := json.MarshalIndent(model.StagingSeq{StagingGeneration: stage.StagingGeneration}, "", "  ")
	return os.WriteFile(seqPath, append(seqRaw, '\n'), 0o644)
}

func IngestProject(stagePath, seqPath, projectDir string) error {
	project, err := LoadProject(projectDir)
	if err != nil {
		return err
	}
	files, err := LoadAnnotations(projectDir, project.Annotators)
	if err != nil {
		return err
	}
	stage, err := StageAnnotations(project, files)
	if err != nil {
		return err
	}
	stage.ProjectID = project.ProjectID
	return WriteStaging(stagePath, seqPath, projectDir, stage)
}
