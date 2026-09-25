package staging

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"

	"mailindex/internal/model"
)

type digestRow struct {
	MessageID    string `json:"message_id"`
	ThreadRootID string `json:"thread_root_id"`
	DateUnix     int64  `json:"date_unix"`
	Subject      string `json:"subject"`
	IsRoot       bool   `json:"is_root"`
}

func digestRows(list []model.IndexedMessage) []digestRow {
	rows := make([]digestRow, len(list))
	for i, msg := range list {
		rows[i] = digestRow{
			MessageID:    msg.MessageID,
			ThreadRootID: msg.ThreadRootID,
			DateUnix:     msg.DateUnix,
			Subject:      msg.Subject,
			IsRoot:       msg.IsRoot,
		}
	}
	return rows
}

func hashPayload(raw []byte) string {
	sum := sha256.Sum256(raw)
	return fmt.Sprintf("%x", sum[:])
}

func marshalDigestPayload(v any) ([]byte, error) {
	buf := &bytes.Buffer{}
	enc := json.NewEncoder(buf)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		return nil, err
	}
	b := buf.Bytes()
	if len(b) > 0 && b[len(b)-1] == '\n' {
		b = b[:len(b)-1]
	}
	return b, nil
}

func FinalizeIndexDigest(list []model.IndexedMessage, _ int) string {
	raw, err := marshalDigestPayload(digestRows(list))
	if err != nil {
		return ""
	}
	return hashPayload(raw)
}

func VerifyIndexDigest(snap model.IndexSnapshot) error {
	expect := FinalizeIndexDigest(snap.MessagesIndexedList, snap.ThreadsResolved)
	if snap.IndexDigest != expect {
		return fmt.Errorf("index digest mismatch")
	}
	return nil
}
