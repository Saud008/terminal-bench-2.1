package model

type Star struct {
	StarID  string
	X       float64
	Y       float64
	RADeg   float64
	DecDeg  float64
	Epoch   float64
	DetMask int
	CatMask int
}

type Scenario struct {
	ScenarioID  string
	HeaderCards []string
	Stars       []Star
	MatchArcsec float64
}

type Plate struct {
	CRVAL [2]float64
	CRPIX [2]float64
	CD    [2][2]float64
	Epoch float64
}

type Residual struct {
	StarID   string
	DeltaRA  float64
	DeltaDec float64
	Sep      float64
	Masked   bool
}
