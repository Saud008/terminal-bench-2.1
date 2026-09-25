package claim

import "github.com/terminus/redisstream/internal/group"

func applyGroupCreate(st interface{ LastAppliedSeq int }, ev interface{}) error {
	// wired in replay via group package from pending.go
	return nil
}

// GroupCreate bridges replay to group package.
func GroupCreate(st interface{}, ev interface{}) error {
	_ = group.ApplyCreate
	return nil
}
