package model

type Config struct {
	StagingPath             string `json:"staging_path"`
	StagingSeqPath          string `json:"staging_seq_path"`
	ConsensusGenerationPath string `json:"consensus_generation_path"`
	ConsensusExportPath     string `json:"consensus_export_path"`
}

type Annotator struct {
	ID          string  `json:"id"`
	Weight      float64 `json:"weight"`
	Adjudicator bool    `json:"adjudicator,omitempty"`
}

type Document struct {
	DocID    string `json:"doc_id"`
	Revision int    `json:"revision"`
	TextLen  int    `json:"text_len"`
}

type RevisionEntry struct {
	CurrentRevision int            `json:"current_revision"`
	Shifts          map[string]int `json:"shifts"`
}

type Project struct {
	ProjectID    string                    `json:"project_id"`
	Documents    []Document                `json:"documents"`
	Annotators   []Annotator               `json:"annotators"`
	RevisionMap  map[string]RevisionEntry  `json:"revision_map"`
}

type LockRef struct {
	Kind   string `json:"kind"`
	DocID  string `json:"doc_id"`
	SpanID string `json:"span_id,omitempty"`
	RelID  string `json:"relation_id,omitempty"`
}

type SpanAnnotation struct {
	ID       string `json:"id"`
	DocID    string `json:"doc_id"`
	Revision int    `json:"revision"`
	Start    int    `json:"start"`
	End      int    `json:"end"`
	Label    string `json:"label"`
}

type RelationAnnotation struct {
	ID    string `json:"id"`
	DocID string `json:"doc_id"`
	From  string `json:"from"`
	To    string `json:"to"`
	Type  string `json:"type"`
}

type AnnotationFile struct {
	Annotator string               `json:"annotator"`
	Locks     []LockRef            `json:"locks"`
	Spans     []SpanAnnotation     `json:"spans"`
	Relations []RelationAnnotation `json:"relations"`
}

type StagedSpan struct {
	SourceID   string  `json:"source_id"`
	Annotator  string  `json:"annotator"`
	DocID      string  `json:"doc_id"`
	Revision   int     `json:"revision"`
	Start      int     `json:"start"`
	End        int     `json:"end"`
	Label      string  `json:"label"`
	Weight     float64 `json:"weight"`
	Locked     bool    `json:"locked"`
}

type StagedRelation struct {
	SourceID  string  `json:"source_id"`
	Annotator string  `json:"annotator"`
	DocID     string  `json:"doc_id"`
	From      string  `json:"from"`
	To        string  `json:"to"`
	Type      string  `json:"type"`
	Weight    float64 `json:"weight"`
	Locked    bool    `json:"locked"`
}

type AnnotationStaging struct {
	ProjectID         string           `json:"project_id"`
	ProjectPath       string           `json:"project_path"`
	ProjectDigest     string           `json:"project_digest"`
	Project           Project          `json:"project"`
	Spans             []StagedSpan     `json:"spans"`
	Relations         []StagedRelation `json:"relations"`
	StagingGeneration int              `json:"staging_generation"`
}

type StagingSeq struct {
	StagingGeneration int `json:"staging_generation"`
}

type ConsensusSpan struct {
	ID      string  `json:"id"`
	DocID   string  `json:"doc_id"`
	Start   int     `json:"start"`
	End     int     `json:"end"`
	Label   string  `json:"label"`
	Score   float64 `json:"score"`
	Locked  bool    `json:"locked"`
}

type ConsensusRelation struct {
	ID         string  `json:"id"`
	DocID      string  `json:"doc_id"`
	Arg1Span   string  `json:"arg1_span"`
	Arg2Span   string  `json:"arg2_span"`
	Type       string  `json:"type"`
	Score      float64 `json:"score"`
	Locked     bool    `json:"locked"`
}

type ConsensusGeneration struct {
	Generation        int                 `json:"generation"`
	StagingGeneration int                 `json:"staging_generation"`
	ProjectDigest     string              `json:"project_digest"`
	Spans             []ConsensusSpan     `json:"spans"`
	Relations         []ConsensusRelation `json:"relations"`
}

type ConsensusExport struct {
	ProjectID           string              `json:"project_id"`
	StagingGeneration   int                 `json:"staging_generation"`
	ConsensusGeneration int                 `json:"consensus_generation"`
	Spans               []ConsensusSpan     `json:"spans"`
	Relations           []ConsensusRelation `json:"relations"`
	ConsensusDigest     string              `json:"consensus_digest"`
}
