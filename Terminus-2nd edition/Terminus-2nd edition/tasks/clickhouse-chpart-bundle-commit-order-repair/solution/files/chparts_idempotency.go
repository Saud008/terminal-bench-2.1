package ingest

import "github.com/clickparts/chparts/internal/store"

func ShouldSkipReplay(st *store.Store, key string) (bool, error) {
	return st.HasIngestKey(key)
}

func RecordReplay(st *store.Store, key, partID string) error {
	return st.RecordIngestKey(key, partID)
}

func IngestKey(batchID, partID string) string {
	return batchID + ":" + partID
}
