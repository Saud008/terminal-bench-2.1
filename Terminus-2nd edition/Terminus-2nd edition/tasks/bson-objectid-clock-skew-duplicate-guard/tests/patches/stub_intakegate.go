package intakegate

import (
	"fmt"
	"time"

	"github.com/terminus/wireclock/pkg/oidstore"
	"github.com/terminus/wireclock/pkg/wireframe"
	"github.com/terminus/wireclock/pkg/objclock"
	"github.com/terminus/wireclock/pkg/digestseal"
	"github.com/terminus/wireclock/pkg/durastore"
)

type Document = wireframe.AdmitDocument
type Result = wireframe.AdmitResult

type Service struct {
	DB        *durastore.DB
	Generator *objclock.Generator
	MachineID string
}

func NewService(db *durastore.DB, gen *objclock.Generator, machineID string) *Service {
	return &Service{DB: db, Generator: gen, MachineID: machineID}
}

func (s *Service) AdmitBatch(nowUnix int64, docs []Document) ([]Result, error) {
	sealDocs := oidstore.ToSealDocs(docs)
	if err := digestseal.WriteBatchSnapshot(digestseal.BatchSnapshotPath, s.MachineID, nowUnix, sealDocs); err != nil {
		return nil, err
	}
	return oidstore.CommitBatch(s.DB, s.Generator, s.MachineID, digestseal.BatchSnapshotPath, docs)
}

func (s *Service) Count() (int, error) {
	var n int
	err := s.DB.SQL.QueryRow(`SELECT COUNT(*) FROM documents`).Scan(&n)
	return n, err
}

func (s *Service) PayloadFor(machineID string, seq int) (string, error) {
	var p string
	err := s.DB.SQL.QueryRow(
		`SELECT payload_json FROM documents WHERE machine_id = ? AND client_seq = ?`,
		machineID, seq,
	).Scan(&p)
	return p, err
}

func (s *Service) TouchClock(nowUnix int64) {
	_, _ = s.DB.SQL.Exec(
		`INSERT INTO admit_meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value`,
		"last_clock", fmt.Sprintf("%d", nowUnix),
	)
}

func (s *Service) Now() int64 {
	return time.Now().Unix()
}
