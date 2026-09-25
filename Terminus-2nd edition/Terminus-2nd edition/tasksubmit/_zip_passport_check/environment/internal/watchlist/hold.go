package watchlist

import "github.com/terminus/borderdocctl/internal/model"

// HasBlockingHold returns true when an active hold blocks the holder.
func HasBlockingHold(holderID string, holds []model.Hold) bool {
	for _, h := range holds {
		if h.HolderID == holderID && !h.Active {
			return true
		}
	}
	return false
}
