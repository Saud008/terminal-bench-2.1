package relation

import "github.com/terminus/brat-consensus-exporter/internal/model"

func Normalize(rel model.StagedRelation, spanID map[string]string) model.StagedRelation {
	arg1 := spanID[rel.From]
	arg2 := spanID[rel.To]
	if arg1 == "" {
		arg1 = rel.From
	}
	if arg2 == "" {
		arg2 = rel.To
	}
	return model.StagedRelation{
		SourceID: rel.SourceID, Annotator: rel.Annotator, DocID: rel.DocID,
		From: arg2, To: arg1, Type: rel.Type, Weight: rel.Weight, Locked: rel.Locked,
	}
}

func MapRelations(rels []model.StagedRelation, spanID map[string]string) []model.StagedRelation {
	out := make([]model.StagedRelation, 0, len(rels))
	for _, r := range rels {
		out = append(out, Normalize(r, spanID))
	}
	return out
}
