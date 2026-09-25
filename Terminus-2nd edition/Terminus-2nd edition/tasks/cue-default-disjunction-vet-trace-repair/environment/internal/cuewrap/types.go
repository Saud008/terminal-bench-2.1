package cuewrap

type FieldType string

const (
	TypeString   FieldType = "string"
	TypeInt      FieldType = "int"
	TypeDisjunct FieldType = "disjunct"
)

type FieldSpec struct {
	Name      string
	Optional  bool
	Type      FieldType
	Disjuncts []string
}

type SchemaSpec struct {
	Name   string
	Closed bool
	Embed  string
	Fields []FieldSpec
	File   string
	Line   int
}

type ConfigSpec struct {
	ID         string
	Schema     string
	Fields     map[string]ConfigValue
	FieldOrder []string
	File       string
	Line       int
}

type ConfigValue struct {
	Literal   string
	UseDisjunct bool
	File      string
	Line      int
}

type VetRule struct {
	Path  string
	Attr  string
	File  string
	Line  int
}

type ExportRule struct {
	Path string
	Kind string
	File string
	Line int
}

type Workspace struct {
	Dir      string
	Name     string
	Includes []string
	Schemas  map[string]SchemaSpec
	Configs  map[string]ConfigSpec
	VetRules []VetRule
	Exports  []ExportRule
}

type EvalResult struct {
	Values map[string]any
}

type VetTrace struct {
	Path    string   `json:"path"`
	Attr    string   `json:"attr"`
	Lineage []string `json:"lineage"`
	Detail  string   `json:"detail"`
}

type VetDoc struct {
	Workspace string     `json:"workspace"`
	Seed      string     `json:"seed"`
	OK        bool       `json:"ok"`
	Error     string     `json:"error,omitempty"`
	Traces    []VetTrace `json:"traces"`
}

type ProvenanceRow struct {
	Path   string `json:"path"`
	Kind   string `json:"kind"`
	Source string `json:"source"`
}

type ExportDoc struct {
	Workspace  string            `json:"workspace"`
	Seed       string            `json:"seed"`
	Values     map[string]any    `json:"values"`
	Provenance []ProvenanceRow   `json:"provenance"`
}

type FlatSchema struct {
	Chain  []string
	Fields map[string]FieldSpec
	Closed bool
}
