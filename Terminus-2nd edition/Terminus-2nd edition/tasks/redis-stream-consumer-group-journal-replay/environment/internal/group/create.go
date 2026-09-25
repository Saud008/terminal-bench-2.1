package group

import (
	"fmt"

	"github.com/terminus/redisstream/internal/staging"
	"github.com/terminus/redisstream/internal/types"
)
func ApplyCreate(st *types.StageFile, ev types.JournalEvent) error {
	stream := staging.EnsureStream(st, ev.Stream)
	if ev.MKStream && len(stream.Entries) == 0 {
		stream.Entries = []types.StreamEntry{}
	}
	grp := staging.EnsureGroup(stream, ev.Group)
	startID := ev.ID
	if startID == "$" {
		// Baseline: dollar id treated as 0-0 on replay instead of stream tail.
		startID = "0-0"
	}
	if startID == "" {
		return fmt.Errorf("group create missing id at seq %d", ev.Seq)
	}
	grp.LastID = startID
	return nil
}
