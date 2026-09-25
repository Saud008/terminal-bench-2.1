package revision

import (
	"fmt"
	"strconv"

	"github.com/terminus/brat-consensus-exporter/internal/model"
)

func NormalizeSpan(project model.Project, span model.StagedSpan) model.StagedSpan {
	entry, ok := project.RevisionMap[span.DocID]
	if !ok {
		return span
	}
	shift := 0
	return model.StagedSpan{
		SourceID: span.SourceID, Annotator: span.Annotator, DocID: span.DocID,
		Revision: entry.CurrentRevision, Start: span.Start + shift, End: span.End + shift,
		Label: span.Label, Weight: span.Weight, Locked: span.Locked,
	}
}

func RevisionKey(docID string, revision int) string {
	return fmt.Sprintf("%s@%d", docID, revision)
}

func ShiftFor(project model.Project, docID string, revision int) int {
	entry, ok := project.RevisionMap[docID]
	if !ok {
		return 0
	}
	v, ok := entry.Shifts[strconv.Itoa(revision)]
	if !ok {
		return 0
	}
	return v
}
