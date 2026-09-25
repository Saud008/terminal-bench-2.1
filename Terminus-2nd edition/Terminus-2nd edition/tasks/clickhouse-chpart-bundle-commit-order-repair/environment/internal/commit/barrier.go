package commit

import "github.com/clickparts/chparts/internal/store"

func FinalizeCommit(st *store.Store, maxBlock int64) error {
	return st.SetMaxBlock(maxBlock)
}
