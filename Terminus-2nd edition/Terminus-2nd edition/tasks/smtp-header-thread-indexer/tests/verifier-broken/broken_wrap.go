package export

import (
	"sort"

	"mailindex/internal/model"
)

// BuildReport assembles the export document from a snapshot. Broken: re-sorts
// messages_indexed_list by message_id instead of preserving assign-stage order.
func BuildReport(snap model.IndexSnapshot) model.Report {
	list := append([]model.IndexedMessage(nil), snap.MessagesIndexedList...)
	sort.Slice(list, func(i, j int) bool {
		return list[i].MessageID < list[j].MessageID
	})
	return model.Report{
		IndexVersion:             snap.IndexVersion,
		FilesRead:                snap.FilesRead,
		MessagesIn:               snap.MessagesIn,
		MessagesIndexed:          snap.MessagesIndexed,
		MessagesSkippedMalformed: snap.MessagesSkippedMalformed,
		MessagesDeduped:          snap.MessagesDeduped,
		ThreadsResolved:          snap.ThreadsResolved,
		MessagesIndexedList:      list,
	}
}
