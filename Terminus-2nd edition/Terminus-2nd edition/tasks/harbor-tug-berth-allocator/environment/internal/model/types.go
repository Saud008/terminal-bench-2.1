package model

// DispatchRow is one JSONL ingest record.
type DispatchRow struct {
	VoyageID     string `json:"voyage_id"`
	MMSI         int64  `json:"mmsi"`
	BerthID      string `json:"berth_id"`
	ArrivalUTC   string `json:"arrival_utc"`
	DepartureUTC string `json:"departure_utc"`
	NmeaRaw      string `json:"nmea_raw"`
}

// SnapshotRow is persisted in ingest-snapshot.json.
type SnapshotRow struct {
	VoyageID     string `json:"voyage_id"`
	MMSI         int64  `json:"mmsi"`
	BerthID      string `json:"berth_id"`
	ArrivalUTC   string `json:"arrival_utc"`
	DepartureUTC string `json:"departure_utc"`
}
