package model

type KeyPolicy struct {
	Type                         string `json:"type"`
	MinDecryptionVersion         int    `json:"min_decryption_version"`
	DeletionAllowed              bool   `json:"deletion_allowed"`
	ConvergentEncryption         bool   `json:"convergent_encryption"`
	Exportable                   bool   `json:"exportable"`
	SoftRotationHaltAfterVersion int    `json:"soft_rotation_halt_after_version"`
}

type VersionEntry struct {
	Version   int  `json:"version"`
	Active    bool `json:"active"`
	Deleted   bool `json:"deleted"`
	CreatedAt int64 `json:"creation_time"`
}

type KeyState struct {
	Name                 string         `json:"name"`
	Policy               KeyPolicy      `json:"policy"`
	Versions             []VersionEntry `json:"versions"`
	LatestVersion        int            `json:"latest_version"`
	MinDecryptionVersion int            `json:"min_decryption_version"`
	SoftHaltAfter        int            `json:"soft_rotation_halt_after_version"`
}

type EncryptRequest struct {
	Plaintext string `json:"plaintext"`
	Context   string `json:"context"`
	KeyVersion int   `json:"key_version"`
}

type DecryptRequest struct {
	Ciphertext string `json:"ciphertext"`
}

type BatchItem struct {
	Plaintext string `json:"plaintext"`
	Context   string `json:"context"`
}

type BatchRequest struct {
	BatchInput []BatchItem `json:"batch_input"`
}

type BatchResult struct {
	Ciphertext string `json:"ciphertext"`
	KeyVersion int    `json:"key_version"`
}

type BatchResponse struct {
	BatchResults []BatchResult `json:"batch_results"`
}

type PolicyLoadRequest struct {
	PolicyFile string `json:"policy_file"`
}
