package model

type Program struct {
    ProgramID   string `json:"program_id"`
    FeedID      string `json:"feed_id"`
    StartUTC    string `json:"start_utc"`
    DurationSec int    `json:"duration_sec"`
    Title       string `json:"title"`
}

type RightsContract struct {
    ContractID  string `json:"contract_id"`
    ProgramID   string `json:"program_id"`
    Region      string `json:"region"`
    WindowStart string `json:"window_start"`
    WindowEnd   string `json:"window_end"`
}

type Blackout struct {
    BlackoutID string `json:"blackout_id"`
    Region     string `json:"region"`
    StartUTC   string `json:"start_utc"`
    EndUTC     string `json:"end_utc"`
    Precedence int    `json:"precedence"`
}

type AdMarker struct {
    ProgramID string `json:"program_id"`
    OffsetSec int    `json:"offset_sec"`
    MarkerID  string `json:"marker_id"`
}

type Feed struct {
    FeedID         string            `json:"feed_id"`
    Substitutions  map[string]string `json:"substitutions"`
}

type Policies struct {
    OverlapRule string `json:"overlap_rule"`
}

type ScheduleBundle struct {
    Seed       string           `json:"seed"`
    Channel    string           `json:"channel"`
    Region     string           `json:"region"`
    Programs   []Program        `json:"programs"`
    Rights     []RightsContract `json:"rights"`
    Blackouts  []Blackout       `json:"blackouts"`
    AdMarkers  []AdMarker       `json:"ad_markers"`
    Feeds      []Feed           `json:"feeds"`
    Policies   Policies         `json:"policies"`
}

type PlanEntry struct {
    ProgramID string `json:"program_id"`
    FeedID    string `json:"feed_id"`
    StartUTC  string `json:"start_utc"`
    Region    string `json:"region"`
    Status    string `json:"status"`
    RunStamp  string `json:"run_stamp"`
}
