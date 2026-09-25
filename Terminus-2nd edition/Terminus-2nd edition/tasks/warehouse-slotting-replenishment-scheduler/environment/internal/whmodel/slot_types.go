package whmodel

type Policies struct {
	HeadroomMargin int `json:"headroom_margin"`
	MinKeepUnits   int `json:"min_keep_units"`
	ReorderPct     int `json:"reorder_pct"`
}

type SKU struct {
	SKUID        string `json:"sku_id"`
	PicksPerDay  int    `json:"picks_per_day"`
	OnHandPct    int    `json:"on_hand_pct"`
	PalletUnits  int    `json:"pallet_units"`
	PickFaceSlot string `json:"pick_face_slot"`
	CurrentUnits int    `json:"current_units"`
}

type Slot struct {
	SlotID        string `json:"slot_id"`
	CapacityUnits int    `json:"capacity_units"`
	Zone          string `json:"zone"`
}

type Worker struct {
	WorkerID   string `json:"worker_id"`
	ShiftStart int    `json:"shift_start"`
	ShiftEnd   int    `json:"shift_end"`
}

type Bundle struct {
	ScenarioID string   `json:"scenario_id"`
	WaveID     string   `json:"wave_id"`
	Policies   Policies `json:"policies"`
	SKUs       []SKU    `json:"skus"`
	Slots      []Slot   `json:"slots"`
	Workers    []Worker `json:"workers"`
}
