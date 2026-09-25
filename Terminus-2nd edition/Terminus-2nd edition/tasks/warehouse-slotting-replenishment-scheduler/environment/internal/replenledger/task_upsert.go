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
	_, err := db.Exec(`INSERT INTO wave_tasks(task_key,sku_id,slot_id,units,start_minute,end_minute) VALUES(?,?,?,?,?,?)`,
		row.TaskKey, row.SKUID, row.SlotID, row.Units, row.StartMinute, row.EndMinute)
	return err
}

func BindWorker(db *sql.DB, taskKey, workerID string) error {
	_, err := db.Exec(`UPDATE wave_tasks SET worker_id=? WHERE task_key=?`, workerID, taskKey)
	return err
}
