package emergaudit

import "database/sql"

type Record struct {
	PatientID  string
	UnitID     string
	Authorizer string
	Reason     string
	IssuedAt   string
}

func Lookup(db *sql.DB, patientID, unitID string) (*Record, error) {
	var rec Record
	err := db.QueryRow(`SELECT patient_id, unit_id, authorizer, reason, issued_at FROM overrides WHERE patient_id=? AND unit_id=?`,
		patientID, unitID).Scan(&rec.PatientID, &rec.UnitID, &rec.Authorizer, &rec.Reason, &rec.IssuedAt)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &rec, nil
}
