package lock

import "github.com/terminus/brat-consensus-exporter/internal/model"

func FilterLockedSpans(spans []model.StagedSpan) []model.StagedSpan {
	return spans
}

func FilterLockedRelations(rels []model.StagedRelation) []model.StagedRelation {
	return rels
}

func PreferLocks(spans []model.StagedSpan) []model.StagedSpan {
	return spans
}
