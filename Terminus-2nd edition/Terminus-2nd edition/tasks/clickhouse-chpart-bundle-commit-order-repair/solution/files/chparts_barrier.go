package commit

import "github.com/clickparts/chparts/internal/store"

func FinalizeCommit(st *store.Store, maxBlock int64) error {
	if err := st.SetFsynced(true); err != nil {
		return err
	}
	return st.SetMaxBlock(maxBlock)
}
