package oidstore

import (
	"database/sql"
	"fmt"

	"github.com/terminus/wireclock/pkg/wireframe"
	"github.com/terminus/wireclock/pkg/objclock"
	"github.com/terminus/wireclock/pkg/digestseal"
	"github.com/terminus/wireclock/pkg/durastore"
)

func CommitBatch(db *durastore.DB, gen *objclock.Generator, machineID string, snapPath string, liveDocs []wireframe.AdmitDocument) ([]wireframe.AdmitResult, error) {
	_ = snapPath
	var out []wireframe.AdmitResult
	for _, doc := range liveDocs {
		res, err := commitOne(db, gen, machineID, 0, doc)
		if err != nil {
			return nil, err
		}
		out = append(out, res)
	}
	return out, nil
}

func commitOne(db *durastore.DB, gen *objclock.Generator, machineID string, nowUnix int64, doc wireframe.AdmitDocument) (wireframe.AdmitResult, error) {
	existing, err := lookupClient(db, machineID, doc.ClientSeq)
	if err != nil {
		return wireframe.AdmitResult{}, err
	}
	if existing != "" {
		_, _ = db.SQL.Exec(
			`UPDATE documents SET payload_json = ?, claimed_at = ? WHERE machine_id = ? AND client_seq = ?`,
			string(doc.Payload), nowUnix, machineID, doc.ClientSeq,
		)
		return wireframe.AdmitResult{ID: existing, ClientSeq: doc.ClientSeq, RepeatClaim: true}, nil
	}

	id, err := gen.Generate(nowUnix)
	if err != nil {
		return wireframe.AdmitResult{}, err
	}
	_, err = db.SQL.Exec(
		`INSERT INTO documents (_id, machine_id, client_seq, payload_json, claimed_at) VALUES (?, ?, ?, ?, ?)`,
		id.Hex(), machineID, doc.ClientSeq, string(doc.Payload), nowUnix,
	)
	if err != nil {
		return wireframe.AdmitResult{}, err
	}
	_ = setMeta(db, "last_clock", fmt.Sprintf("%d", nowUnix))
	return wireframe.AdmitResult{ID: id.Hex(), ClientSeq: doc.ClientSeq, RepeatClaim: false}, nil
}

func lookupClient(db *durastore.DB, machineID string, seq int) (string, error) {
	var id string
	err := db.SQL.QueryRow(
		`SELECT _id FROM documents WHERE machine_id = ? AND client_seq = ?`,
		machineID, seq,
	).Scan(&id)
	if err == sql.ErrNoRows {
		return "", nil
	}
	return id, err
}

func setMeta(db *durastore.DB, key, value string) error {
	_, err := db.SQL.Exec(
		`INSERT INTO admit_meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value`,
		key, value,
	)
	return err
}

func ToSealDocs(docs []wireframe.AdmitDocument) []digestseal.BatchDocument {
	out := make([]digestseal.BatchDocument, len(docs))
	for i, d := range docs {
		out[i] = digestseal.BatchDocument{ClientSeq: d.ClientSeq, Payload: d.Payload}
	}
	return out
}
