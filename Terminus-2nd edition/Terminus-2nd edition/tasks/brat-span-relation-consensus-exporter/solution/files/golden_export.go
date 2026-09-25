package export

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/brat-consensus-exporter/internal/consensus"
	"github.com/terminus/brat-consensus-exporter/internal/digest"
	"github.com/terminus/brat-consensus-exporter/internal/model"
	"github.com/terminus/brat-consensus-exporter/internal/staging"
)

func RunExport(stagePath, genPath, outPath string) error {
	stage, err := staging.Read(stagePath)
	if err != nil {
		return err
	}
	gen, err := consensus.ReadGeneration(genPath)
	if err != nil {
		return err
	}
	if gen.Generation == 0 {
		return os.ErrInvalid
	}
	if gen.StagingGeneration != stage.StagingGeneration || gen.ProjectDigest != stage.ProjectDigest {
		return fmt.Errorf("consensus state drifted from staging: generation or project_digest mismatch")
	}
	// Use empty slice literals so JSON emits [] rather than null when gen has no rows.
	spans := append([]model.ConsensusSpan{}, gen.Spans...)
	rels := append([]model.ConsensusRelation{}, gen.Relations...)
	sort.Slice(spans, func(i, j int) bool {
		if spans[i].DocID != spans[j].DocID {
			return spans[i].DocID < spans[j].DocID
		}
		if spans[i].Start != spans[j].Start {
			return spans[i].Start < spans[j].Start
		}
		return spans[i].End < spans[j].End
	})
	sort.Slice(rels, func(i, j int) bool {
		if rels[i].DocID != rels[j].DocID {
			return rels[i].DocID < rels[j].DocID
		}
		if rels[i].Arg1Span != rels[j].Arg1Span {
			return rels[i].Arg1Span < rels[j].Arg1Span
		}
		return rels[i].Arg2Span < rels[j].Arg2Span
	})
	exp := model.ConsensusExport{
		ProjectID:           stage.ProjectID,
		StagingGeneration:   stage.StagingGeneration,
		ConsensusGeneration: gen.Generation,
		Spans:               spans,
		Relations:           rels,
		ConsensusDigest:     digest.ConsensusDigest(stage.ProjectID, spans, rels),
	}
	raw, err := json.MarshalIndent(exp, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	return os.WriteFile(outPath, append(raw, '\n'), 0o644)
}
