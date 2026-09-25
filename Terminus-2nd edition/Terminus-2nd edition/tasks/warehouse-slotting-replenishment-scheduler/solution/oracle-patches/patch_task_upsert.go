package replenledger

import "database/sql"

type TaskRow struct {
	TaskKey     string
	SKUID       string
	SlotID      string
	Units       int
	StartMinute int
	EndMinute   int
}

func UpsertTask(db *sql.DB, row TaskRow) error {
	_, err := db.Exec(`INSERT INTO wave_tasks(task_key,sku_id,slot_id,units,start_minute,end_minute) VALUES(?,?,?,?,?,?)
		ON CONFLICT(task_key) DO UPDATE SET units=excluded.units,start_minute=excluded.start_minute,end_minute=excluded.end_minute`,
		row.TaskKey, row.SKUID, row.SlotID, row.Units, row.StartMinute, row.EndMinute)
	return err
}
