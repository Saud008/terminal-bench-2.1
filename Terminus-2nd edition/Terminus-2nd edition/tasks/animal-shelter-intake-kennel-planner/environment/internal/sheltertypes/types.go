package sheltertypes

type SpeciesProfile struct {
    SpeciesCode   string `json:"species_code"`
    Name          string `json:"name"`
    IsolationRank int    `json:"isolation_rank"`
}

type Kennel struct {
    KennelID    string `json:"kennel_id"`
    SpeciesCode string `json:"species_code"`
    Capacity    int    `json:"capacity"`
    Zone        string `json:"zone"`
}

type IntakeRecord struct {
    IntakeID       string  `json:"intake_id"`
    AnimalID       string  `json:"animal_id"`
    SpeciesCode    string  `json:"species_code"`
    VaccValidUntil string  `json:"vacc_valid_until"`
    HoldType       string  `json:"hold_type"`
    SurrenderProb  float64 `json:"surrender_prob"`
    IntakeRank     int     `json:"intake_rank"`
}

type QuarantineWindow struct {
    KennelID  string `json:"kennel_id"`
    StartDate string `json:"start_date"`
    EndDate   string `json:"end_date"`
}

type VaccinationPolicy struct {
    SpeciesCode  string `json:"species_code"`
    MinValidDays int    `json:"min_valid_days"`
}

type KennelCompatRule struct {
    FromSpecies string `json:"from_species"`
    ToSpecies   string `json:"to_species"`
}

type TransferPenalty struct {
    FromSpecies     string `json:"from_species"`
    ToSpecies       string `json:"to_species"`
    TransferPenalty int    `json:"transfer_penalty"`
}

type AdoptionHold struct {
    HoldType       string `json:"hold_type"`
    PrecedenceRank int    `json:"precedence_rank"`
}

type KennelPlacement struct {
    IntakeID    string `json:"intake_id"`
    AnimalID    string `json:"animal_id"`
    KennelID    string `json:"kennel_id"`
    SpeciesCode string `json:"species_code"`
}

type TransferEntry struct {
    IntakeID        string `json:"intake_id"`
    AnimalID        string `json:"animal_id"`
    FromSpecies     string `json:"from_species"`
    ToSpecies       string `json:"to_species"`
    TransferPenalty int    `json:"transfer_penalty"`
}

type ScenarioMeta struct {
    Scenario    string `json:"scenario"`
    IntakeDate  string `json:"intake_date"`
    CatalogSeed string `json:"catalog_seed"`
}

type PriorityScore struct {
    IntakeID      string  `json:"intake_id"`
    AnimalID      string  `json:"animal_id"`
    PriorityScore float64 `json:"priority_score"`
}

type BindArtifact struct {
    RunID           string          `json:"run_id"`
    Scenario        string          `json:"scenario"`
    RegistryPath    string          `json:"registry_path"`
    ArrivalsPath    string          `json:"arrivals_path"`
    RegistryDigest  string          `json:"registry_digest"`
    KennelCount     int             `json:"kennel_count"`
    QuarantineCount int             `json:"quarantine_count"`
    PriorityScores  []PriorityScore `json:"priority_scores"`
}

type WeaveHeader struct {
    RunID      string            `json:"run_id"`
    Scenario   string            `json:"scenario"`
    Engine     string            `json:"engine"`
    RunStamp   string            `json:"run_stamp"`
    WeavePass  int               `json:"weave_pass"`
    Placements []KennelPlacement `json:"placements"`
    Transfers  []TransferEntry   `json:"transfers"`
}
