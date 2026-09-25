package model

type Branch struct {
    BranchID                 string `json:"branch_id"`
    Name                     string `json:"name"`
    AllowsInterbranchTransfer bool   `json:"allows_interbranch_transfer"`
}

type Patron struct {
    PatronID      string `json:"patron_id"`
    HomeBranchID  string `json:"home_branch_id"`
    PriorityClass string `json:"priority_class"`
}

type HoldRequest struct {
    RequestID       string `json:"request_id"`
    PatronID        string `json:"patron_id"`
    ItemID          string `json:"item_id"`
    PickupBranchID  string `json:"pickup_branch_id"`
    HoldDate        string `json:"hold_date"`
}

type ItemCopy struct {
    CopyID   string `json:"copy_id"`
    ItemID   string `json:"item_id"`
    BranchID string `json:"branch_id"`
    Status   string `json:"status"`
}

type Suspension struct {
    PatronID  string `json:"patron_id"`
    StartDate string `json:"start_date"`
    EndDate   string `json:"end_date"`
}

type PriorityPolicy struct {
    ClassName string `json:"class_name"`
    Rank      int    `json:"rank"`
}

type Assignment struct {
    QueuePos int    `json:"queue_pos"`
    PatronID string `json:"patron_id"`
    RequestID string `json:"request_id"`
    CopyID   string `json:"copy_id"`
    BranchID string `json:"branch_id"`
}

type ScenarioMeta struct {
    Scenario      string `json:"scenario"`
    ReconcileDate string `json:"reconcile_date"`
    CatalogSeed   string `json:"catalog_seed"`
}
