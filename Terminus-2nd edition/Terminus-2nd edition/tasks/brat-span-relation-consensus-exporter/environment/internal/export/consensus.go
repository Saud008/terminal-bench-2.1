package export

import (
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/brat-consensus-exporter/internal/consensus"
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
	spans := append([]model.ConsensusSpan(nil), gen.Spans...)
	rels := append([]model.ConsensusRelation(nil), gen.Relations...)
	_ = rels
	sort.Slice(spans, func(i, j int) bool { return spans[i].ID < spans[j].ID })
	body, _ := json.Marshal(spans)
	sum := md5.Sum(body)
	exp := model.ConsensusExport{
		ProjectID:           stage.ProjectID,
		StagingGeneration:   stage.StagingGeneration,
		ConsensusGeneration: gen.Generation,
		Spans:               gen.Spans,
		Relations:           gen.Relations,
		ConsensusDigest:     "md5:" + hex.EncodeToString(sum[:]),
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
