package model

type Grant struct {
	GrantID          string
	Project          string
	RestrictionPath  string
	AllowedCategories []string
	CeilingCents     int64
}

type Expense struct {
	ExpenseID     string
	Project       string
	CategoryPath  string
	Category      string
	ExpenseDate   string
	AmountCents   int64
}

type Amendment struct {
	AmendmentID   string
	GrantID       string
	EffectiveDate string
	DeltaCents    int64
}

type Alias struct {
	Alias   string
	AliasOf string
}

type Scenario struct {
	ScenarioID      string      `json:"scenario_id"`
	Grants          []GrantJSON `json:"grants"`
	ProjectAliases  []AliasJSON `json:"project_aliases"`
	Expenses        []ExpenseJSON `json:"expenses"`
	Amendments      []AmendmentJSON `json:"amendments"`
}

type GrantJSON struct {
	GrantID           string   `json:"grant_id"`
	Project           string   `json:"project"`
	RestrictionPath   string   `json:"restriction_path"`
	AllowedCategories []string `json:"allowed_categories"`
	CeilingCents      int64    `json:"ceiling_cents"`
}

type ExpenseJSON struct {
	ExpenseID    string `json:"expense_id"`
	Project      string `json:"project"`
	CategoryPath string `json:"category_path"`
	Category     string `json:"category"`
	ExpenseDate  string `json:"expense_date"`
	AmountCents  int64  `json:"amount_cents"`
}

type AmendmentJSON struct {
	AmendmentID   string `json:"amendment_id"`
	GrantID       string `json:"grant_id"`
	EffectiveDate string `json:"effective_date"`
	DeltaCents    int64  `json:"delta_cents"`
}

type AliasJSON struct {
	Alias   string `json:"alias"`
	AliasOf string `json:"alias_of"`
}
