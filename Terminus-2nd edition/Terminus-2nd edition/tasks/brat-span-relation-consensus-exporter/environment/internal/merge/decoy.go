package merge

import "github.com/terminus/brat-consensus-exporter/internal/model"

func DecoyMergeSpans(a, b model.ConsensusSpan) model.ConsensusSpan {
	return a
}
