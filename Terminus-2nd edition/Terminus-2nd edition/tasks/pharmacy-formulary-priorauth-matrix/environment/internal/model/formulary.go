package model

type Drug struct {
    NDC     string  `json:"ndc"`
    RxNorm  string  `json:"rxnorm"`
    Name    string  `json:"name"`
    Aliases []Alias `json:"aliases"`
}

type Alias struct {
    Code string `json:"code"`
    Rank int    `json:"rank"`
}

type Plan struct {
    PlanID string `json:"plan_id"`
    Name   string `json:"name"`
}

type Override struct {
    PlanID         string `json:"plan_id"`
    NDC            string `json:"ndc"`
    PaRequired     bool   `json:"pa_required"`
    Priority       int    `json:"priority"`
    EffectiveStart string `json:"effective_start"`
    EffectiveEnd   string `json:"effective_end"`
}

type StepLink struct {
    PlanID           string `json:"plan_id"`
    TargetNDC        string `json:"target_ndc"`
    PrerequisiteNDC  string `json:"prerequisite_ndc"`
    Sequence         int    `json:"sequence"`
}

type ScenarioJSON struct {
    Scenario    string     `json:"scenario"`
    AsOf        string     `json:"as_of"`
    Drugs       []Drug     `json:"drugs"`
    Plans       []Plan     `json:"plans"`
    Overrides   []Override `json:"overrides"`
    StepChains  []StepLink `json:"step_chains"`
}

type RosterFile struct {
    Engine        string       `json:"engine"`
    Scenario      string       `json:"scenario"`
    AsOf          string       `json:"as_of"`
    Drugs         []Drug       `json:"drugs"`
    Plans         []Plan       `json:"plans"`
    Overrides     []Override   `json:"overrides"`
    StepChains    []StepLink   `json:"step_chains"`
    RosterDigest string       `json:"roster_digest"`
}

type RevisionFile struct {
    RefreshRevision int `json:"refresh_revision"`
}

type MatrixRow struct {
    PlanID          string `json:"plan_id"`
    NDCNormalized   string `json:"ndc_normalized"`
    PreferredRxNorm string `json:"preferred_rxnorm"`
    RequiresPA      bool   `json:"requires_pa"`
    StepComplete    bool   `json:"step_complete"`
    OverrideApplied bool   `json:"override_applied"`
    EffectiveRule   string `json:"effective_rule"`
}

type MatrixReport struct {
    Scenario    string      `json:"scenario"`
    AsOf        string      `json:"as_of"`
    RowCount    int         `json:"row_count"`
    MatrixDigest string     `json:"matrix_digest"`
    Rows        []MatrixRow `json:"rows"`
}
