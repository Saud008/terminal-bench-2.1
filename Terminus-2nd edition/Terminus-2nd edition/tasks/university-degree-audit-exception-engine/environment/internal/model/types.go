package model

type ScenarioMeta struct {
    Scenario    string `json:"scenario"`
    AuditDate   string `json:"audit_date"`
    CatalogYear int    `json:"catalog_year"`
    AuditTerm   string `json:"audit_term"`
    CatalogSeed string `json:"catalog_seed"`
}

type Course struct {
    CourseCode   string  `json:"course_code"`
    Title        string  `json:"title"`
    Credits      float64 `json:"credits"`
    CatalogYear  int     `json:"catalog_year"`
}

type Enrollment struct {
    StudentID    string  `json:"student_id"`
    CourseCode   string  `json:"course_code"`
    Term         string  `json:"term"`
    GradePoints  float64 `json:"grade_points"`
    IsTransfer   bool    `json:"is_transfer"`
}

type TransferEquiv struct {
    SourceCode     string `json:"source_code"`
    TargetCode     string `json:"target_code"`
    ValidFromYear  int    `json:"valid_from_year"`
    ValidToYear    int    `json:"valid_to_year"`
}

type Substitution struct {
    SubReqID         string `json:"sub_req_id"`
    ReplacesReqID    string `json:"replaces_req_id"`
    ExpiresAfterTerm string `json:"expires_after_term"`
}

type Requirement struct {
    ReqID           string  `json:"req_id"`
    ParentReqID     string  `json:"parent_req_id"`
    RequiredCredits float64 `json:"required_credits"`
}

type RequirementCourse struct {
    ReqID      string `json:"req_id"`
    CourseCode string `json:"course_code"`
}

type Waiver struct {
    StudentID string `json:"student_id"`
    ReqID     string `json:"req_id"`
    Reason    string `json:"reason"`
}

type ReqStatus struct {
    ReqID             string  `json:"req_id"`
    SatisfiedCredits  float64 `json:"satisfied_credits"`
    RequiredCredits   float64 `json:"required_credits"`
    Satisfied         bool    `json:"satisfied"`
}
