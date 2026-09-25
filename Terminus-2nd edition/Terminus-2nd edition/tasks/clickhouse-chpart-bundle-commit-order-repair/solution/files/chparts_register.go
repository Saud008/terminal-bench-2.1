package ingest

import (
	"fmt"

	"github.com/clickparts/chparts/internal/model"
	"github.com/clickparts/chparts/internal/store"
)

func RegisterPart(st *store.Store, meta model.PartMeta) error {
	return st.RegisterPart(meta, false)
}

func ApplyChecksum(st *store.Store, partID string, ok bool) error {
	if err := st.MarkChecksumOK(partID, ok); err != nil {
		return err
	}
	if !ok {
		return checksumFail(partID)
	}
	return st.MarkCommitted(partID)
}

func checksumFail(partID string) error {
	return fmt.Errorf("checksum mismatch for %s", partID)
}
