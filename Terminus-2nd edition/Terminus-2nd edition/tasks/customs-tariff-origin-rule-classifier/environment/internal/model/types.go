package model

type ShipmentLine struct {
	LineID         string     `json:"line_id"`
	HSRaw          string     `json:"hs_raw"`
	DeclaredOrigin string     `json:"declared_origin"`
	ValueCents     int64      `json:"value_cents"`
	BOMShares      []BOMShare `json:"bom_shares"`
}

type BOMShare struct {
	Country  string `json:"country"`
	ShareBPS int64  `json:"share_bps"`
}

type Certificate struct {
	CertID        string `json:"cert_id"`
	LineID        string `json:"line_id"`
	AgreementCode string `json:"agreement_code"`
	IssuedOn      string `json:"issued_on"`
	ExpiresOn     string `json:"expires_on"`
	OriginCountry string `json:"origin_country"`
}

type AgreementRule struct {
	AgreementCode string `json:"agreement_code"`
	HSPrefix      string `json:"hs_prefix"`
	RVCMinBPS     int64  `json:"rvc_min_bps"`
	DutyRateBPS   int64  `json:"duty_rate_bps"`
	Priority      int    `json:"priority"`
}

type ClassificationLine struct {
	LineID          string `json:"line_id"`
	HSNormalized    string `json:"hs_normalized"`
	TariffTreatment string `json:"tariff_treatment"`
	AgreementCode   string `json:"agreement_code"`
	RVCBPS          int64  `json:"rvc_bps"`
	CertValid       bool   `json:"cert_valid"`
	DutyRateBPS     int64  `json:"duty_rate_bps"`
}

type ClassificationReport struct {
	ScenarioID      string               `json:"scenario_id"`
	ParsePass       int                  `json:"parse_pass"`
	Classifications []ClassificationLine `json:"classifications"`
	AuditDigest     string               `json:"audit_digest"`
}
