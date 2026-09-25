package model

type Discriminator struct {
	PropertyName string
	Mapping      map[string]string
}

type Schema struct {
	Type                 string
	Types                []string
	Ref                  string
	Properties           map[string]*Schema
	Required             []string
	AllOf                []*Schema
	Default              any
	AdditionalProperties *bool
	Discriminator        *Discriminator
}

type Components struct {
	Schemas map[string]*Schema
}

type MediaType struct {
	Schema *Schema
}

type RequestBody struct {
	Content map[string]*MediaType
}

type Operation struct {
	RequestBody *RequestBody
}

type Spec struct {
	Paths      map[string]map[string]*Operation
	Components *Components
}

type PayloadEnvelope struct {
	Operation string         `json:"operation"`
	Data      map[string]any `json:"data"`
}

type Result struct {
	File       string   `json:"file"`
	Operation  string   `json:"operation"`
	Valid      bool     `json:"valid"`
	Errors     []string `json:"errors"`
	CyclesSeen int      `json:"cycles_seen"`
}

type Stats struct {
	Validated int `json:"validated"`
	Valid     int `json:"valid"`
	Invalid   int `json:"invalid"`
}

type Report struct {
	Seed     string   `json:"seed"`
	Payloads []string `json:"payloads"`
	Results  []Result `json:"results"`
	Stats    Stats    `json:"stats"`
}
