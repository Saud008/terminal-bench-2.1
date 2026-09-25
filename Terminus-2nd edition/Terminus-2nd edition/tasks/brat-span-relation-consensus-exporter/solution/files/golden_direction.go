package relation

import "github.com/terminus/brat-consensus-exporter/internal/model"

func Normalize(rel model.StagedRelation, spanID map[string]string) model.StagedRelation {
	key1 := rel.Annotator + ":" + rel.From
	key2 := rel.Annotator + ":" + rel.To
	arg1 := spanID[key1]
	arg2 := spanID[key2]
	if arg1 == "" {
		arg1 = rel.From
	}
	if arg2 == "" {
		arg2 = rel.To
	}
	return model.StagedRelation{
		SourceID: rel.SourceID, Annotator: rel.Annotator, DocID: rel.DocID,
		From: arg1, To: arg2, Type: rel.Type, Weight: rel.Weight, Locked: rel.Locked,
	}
}

func MapRelations(rels []model.StagedRelation, spanID map[string]string) []model.StagedRelation {
	out := make([]model.StagedRelation, 0, len(rels))
	for _, r := range rels {
		out = append(out, Normalize(r, spanID))
	}
	return out
}
