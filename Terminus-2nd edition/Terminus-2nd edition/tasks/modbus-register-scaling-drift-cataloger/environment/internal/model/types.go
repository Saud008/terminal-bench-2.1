package model

type Config struct {
	StagingPath           string  `json:"staging_path"`
	StagingSeqPath        string  `json:"staging_seq_path"`
	CatalogGenerationPath string  `json:"catalog_generation_path"`
	DriftCatalogPath      string  `json:"drift_catalog_path"`
	RejectedFramesPath    string  `json:"rejected_frames_path"`
	DefaultDriftThreshold float64 `json:"default_drift_threshold"`
}

type ScaleEpoch struct {
	EpochID     string  `json:"epoch_id"`
	EffectiveMs int64   `json:"effective_ms"`
	Factor      float64 `json:"factor"`
	Offset      float64 `json:"offset"`
}

type RegisterOverride struct {
	WordOrder    string `json:"word_order,omitempty"`
	ScaleEpoch   string `json:"scale_epoch,omitempty"`
	ClockSkewMs  int64  `json:"clock_skew_ms,omitempty"`
}

type AlarmSuppression struct {
	DeviceID string `json:"device_id"`
	Register int    `json:"register"`
	StartMs  int64  `json:"start_ms"`
	EndMs    int64  `json:"end_ms"`
}

type Manifest struct {
	DeviceID          string                      `json:"device_id"`
	ClockSkewMs       int64                       `json:"clock_skew_ms"`
	DriftThreshold    float64                     `json:"drift_threshold"`
	DefaultWordOrder  string                      `json:"default_word_order"`
	ScaleEpochs       []ScaleEpoch                `json:"scale_epochs"`
	Baseline          map[string]float64          `json:"baseline"`
	RegisterOverrides map[string]RegisterOverride `json:"register_overrides"`
	AlarmSuppression  []AlarmSuppression          `json:"alarm_suppression"`
}

type Frame struct {
	FrameID        string `json:"frame_id"`
	DeviceID       string `json:"device_id"`
	Register       int    `json:"register"`
	Width          string `json:"width"`
	Words          []int  `json:"words"`
	ReceivedMs     int64  `json:"received_ms"`
	DeviceClockMs  int64  `json:"device_clock_ms"`
}

type PollStaging struct {
	Frames            []Frame `json:"frames"`
	FramesDigest      string  `json:"frames_digest"`
	ManifestSHA256    string  `json:"manifest_sha256"`
	ManifestPath      string  `json:"manifest_path"`
	StagingGeneration int     `json:"staging_generation"`
}

type StagingSeq struct {
	StagingGeneration int `json:"staging_generation"`
}

type CatalogEntry struct {
	FrameID      string  `json:"frame_id"`
	DeviceID     string  `json:"device_id"`
	Register     int     `json:"register"`
	Raw          int64   `json:"raw"`
	Engineering  float64 `json:"engineering"`
	Baseline     float64 `json:"baseline"`
	Drift        float64 `json:"drift"`
	DriftAlarm   bool    `json:"drift_alarm"`
	Suppressed   bool    `json:"suppressed"`
	ScaleEpoch   string  `json:"scale_epoch"`
}

type CatalogGeneration struct {
	Generation        int            `json:"generation"`
	StagingGeneration int            `json:"staging_generation"`
	ManifestSHA256    string         `json:"manifest_sha256"`
	Entries           []CatalogEntry `json:"entries"`
}

type DriftCatalog struct {
	CatalogGeneration int            `json:"catalog_generation"`
	StagingGeneration int            `json:"staging_generation"`
	Entries           []CatalogEntry `json:"entries"`
	CatalogDigest     string         `json:"catalog_digest"`
}

type RejectedFrame struct {
	FrameID string `json:"frame_id"`
	Reason  string `json:"reason"`
}
