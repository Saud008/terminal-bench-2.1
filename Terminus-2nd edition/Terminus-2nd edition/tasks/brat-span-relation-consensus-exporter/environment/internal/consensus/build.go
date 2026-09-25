package consensus

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/brat-consensus-exporter/internal/lock"
	"github.com/terminus/brat-consensus-exporter/internal/model"
	"github.com/terminus/brat-consensus-exporter/internal/relation"
	"github.com/terminus/brat-consensus-exporter/internal/revision"
	"github.com/terminus/brat-consensus-exporter/internal/weight"
)

func Build(stage model.AnnotationStaging) (model.ConsensusGeneration, error) {
	// Staging already carries revision-normalized rows; re-normalize is idempotent
	// when spans sit at current_revision (shift 0). Keep the full set for scoring
	// and namespaced relation span-id mapping after PreferLocks drops losers.
	allNormalized := make([]model.StagedSpan, 0, len(stage.Spans))
	for _, s := range stage.Spans {
		allNormalized = append(allNormalized, revision.NormalizeSpan(stage.Project, s))
	}
	// PreferLocks copies locked spans verbatim, drops unlocked that overlap locks,
	// and runs overlap resolution only on the remaining unlocked spans.
	resolved := lock.PreferLocks(allNormalized)

	consensusSpans := make([]model.ConsensusSpan, 0, len(resolved))
	spanMap := map[string]string{}
	for i, s := range resolved {
		id := fmt.Sprintf("c-s%d", i+1)
		score := weight.ScoreCandidates(collectOverlapGroup(allNormalized, s))
		if s.Locked {
			score = 1000
		}
		consensusSpans = append(consensusSpans, model.ConsensusSpan{
			ID: id, DocID: s.DocID, Start: s.Start, End: s.End, Label: s.Label,
			Score: score, Locked: s.Locked,
		})
		for _, orig := range allNormalized {
			if spansOverlap(orig, s) {
				spanMap[orig.Annotator+":"+orig.SourceID] = id
			}
		}
	}

	mappedRels := relation.MapRelations(stage.Relations, spanMap)
	mappedRels = lock.FilterLockedRelations(mappedRels)
	relGroups := map[string][]model.StagedRelation{}
	for _, r := range mappedRels {
		k := fmt.Sprintf("%s|%s|%s|%s", r.DocID, r.From, r.To, r.Type)
		relGroups[k] = append(relGroups[k], r)
	}
	var keys []string
	for k := range relGroups {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	consensusRels := make([]model.ConsensusRelation, 0)
	for i, k := range keys {
		group := relGroups[k]
		winner := weight.PickRelationByWeight(group)
		score := weight.ScoreRelations(group)
		consensusRels = append(consensusRels, model.ConsensusRelation{
			ID: fmt.Sprintf("c-r%d", i+1), DocID: winner.DocID,
			Arg1Span: winner.From, Arg2Span: winner.To, Type: winner.Type,
			Score: score, Locked: winner.Locked,
		})
	}
	sort.Slice(consensusSpans, func(i, j int) bool {
		if consensusSpans[i].DocID != consensusSpans[j].DocID {
			return consensusSpans[i].DocID < consensusSpans[j].DocID
		}
		if consensusSpans[i].Start != consensusSpans[j].Start {
			return consensusSpans[i].Start < consensusSpans[j].Start
		}
		return consensusSpans[i].End < consensusSpans[j].End
	})
	return model.ConsensusGeneration{
		StagingGeneration: stage.StagingGeneration,
		ProjectDigest:     stage.ProjectDigest,
		Spans:             consensusSpans,
		Relations:         consensusRels,
	}, nil
}

func ReadGeneration(path string) (model.ConsensusGeneration, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.ConsensusGeneration{}, err
	}
	var g model.ConsensusGeneration
	if err := json.Unmarshal(raw, &g); err != nil {
		return model.ConsensusGeneration{}, err
	}
	return g, nil
}

func WriteGeneration(path string, gen model.ConsensusGeneration) error {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	prev, _ := ReadGeneration(path)
	gen.Generation = prev.Generation + 1
	if gen.Generation < 1 {
		gen.Generation = 1
	}
	raw, err := json.MarshalIndent(gen, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(raw, '\n'), 0o644)
}

func RunConsensus(stagePath, genPath string) error {
	stage, err := stagingRead(stagePath)
	if err != nil {
		return err
	}
	gen, err := Build(stage)
	if err != nil {
		return err
	}
	return WriteGeneration(genPath, gen)
}

func stagingRead(path string) (model.AnnotationStaging, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.AnnotationStaging{}, err
	}
	var s model.AnnotationStaging
	if err := json.Unmarshal(raw, &s); err != nil {
		return model.AnnotationStaging{}, err
	}
	return s, nil
}

func spansOverlap(a, b model.StagedSpan) bool {
	return a.DocID == b.DocID && a.Label == b.Label && a.Start < b.End && b.Start < a.End
}

func collectOverlapGroup(all []model.StagedSpan, winner model.StagedSpan) []model.StagedSpan {
	var group []model.StagedSpan
	for _, s := range all {
		if spansOverlap(s, winner) {
			group = append(group, s)
		}
	}
	return group
}
