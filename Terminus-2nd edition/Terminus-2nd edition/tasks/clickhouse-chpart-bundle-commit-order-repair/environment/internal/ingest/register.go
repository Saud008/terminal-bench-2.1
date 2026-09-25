package ingest

import (
	"fmt"

	"github.com/clickparts/chparts/internal/model"
	"github.com/clickparts/chparts/internal/store"
)

func RegisterPart(st *store.Store, meta model.PartMeta) error {
	return st.RegisterPart(meta, true)
}

func ApplyChecksum(st *store.Store, partID string, ok bool) error {
	return st.MarkChecksumOK(partID, ok)
}

func checksumFail(partID string) error {
	return fmt.Errorf("checksum mismatch for %s", partID)
}
