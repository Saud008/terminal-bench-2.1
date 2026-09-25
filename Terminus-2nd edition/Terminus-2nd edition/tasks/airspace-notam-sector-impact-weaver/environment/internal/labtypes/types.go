package labtypes

type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

type NotamRecord struct {
	NotamID    string  `json:"notam_id"`
	SeriesID   string  `json:"series_id"`
	Amendment  int     `json:"amendment"`
	StartMin   int     `json:"start_minute"`
	EndMin     int     `json:"end_minute"`
	Kind       string  `json:"kind"`
	SectorID   string  `json:"sector_id,omitempty"`
	Polygon    []Point `json:"polygon,omitempty"`
	Airport    string  `json:"airport,omitempty"`
	Runway     string  `json:"runway,omitempty"`
	RouteFix   string  `json:"route_fix,omitempty"`
	AirwayID   string  `json:"airway_id,omitempty"`
	ImpactCode string  `json:"impact_code"`
}

type Sector struct {
	SectorID string  `json:"sector_id"`
	Polygon  []Point `json:"polygon"`
}

type FlightPlan struct {
	FlightID   string   `json:"flight_id"`
	RouteFixes []string `json:"route_fixes"`
	Runways    []string `json:"runways,omitempty"`
	Airport    string   `json:"airport,omitempty"`
}

type Airway struct {
	AirwayID string   `json:"airway_id"`
	Fixes    []string `json:"fixes"`
}

type FixPoint struct {
	FixID string  `json:"fix_id"`
	X     float64 `json:"x"`
	Y     float64 `json:"y"`
}

type Policy struct {
	EvalMinute int `json:"eval_minute"`
}

type CampaignBinding struct {
	Engine        string        `json:"engine"`
	Scenario      string        `json:"scenario"`
	Notams        []NotamRecord `json:"notams"`
	Sectors       []Sector      `json:"sectors"`
	Flights       []FlightPlan  `json:"flights"`
	Airways       []Airway      `json:"airways"`
	FixPoints     []FixPoint    `json:"fix_points"`
	Policy        Policy        `json:"policy"`
	BindingDigest string        `json:"binding_digest"`
}

type ChronologyClosure struct {
	Scenario     string        `json:"scenario"`
	ActiveNotams []NotamRecord `json:"active_notams"`
	EvalMinute   int           `json:"eval_minute"`
}

type RouteClosure struct {
	FlightID   string `json:"flight_id"`
	ImpactCode string `json:"impact_code"`
	Detail     string `json:"detail"`
	NotamID    string `json:"notam_id"`
}

type ClosureLattice struct {
	Scenario         string         `json:"scenario"`
	EvalMinute       int            `json:"eval_minute"`
	SealedSectors    []string       `json:"sealed_sectors"`
	RouteClosures    []RouteClosure `json:"route_closures"`
	ActiveNotamCount int            `json:"active_notam_count"`
}

type ImpactClosureAtlas struct {
	Scenario         string         `json:"scenario"`
	EvalMinute       int            `json:"eval_minute"`
	ActiveNotamCount int            `json:"active_notam_count"`
	SealedSectors    []string       `json:"sealed_sectors"`
	RouteClosures    []RouteClosure `json:"route_closures"`
	AtlasDigest      string         `json:"atlas_digest"`
}

type SealEpoch struct {
	SealEpoch int `json:"seal_epoch"`
}
