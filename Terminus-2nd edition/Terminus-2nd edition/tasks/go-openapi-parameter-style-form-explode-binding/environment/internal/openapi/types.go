package openapi

type Document struct {
	Paths map[string]PathItem `yaml:"paths"`
}

type PathItem struct {
	Get  *Operation `yaml:"get,omitempty"`
	Post *Operation `yaml:"post,omitempty"`
}

type Operation struct {
	OperationID string      `yaml:"operationId"`
	Parameters  []Parameter `yaml:"parameters"`
	RequestBody *RequestBody `yaml:"requestBody,omitempty"`
}

type Parameter struct {
	Name     string `yaml:"name"`
	In       string `yaml:"in"`
	Required bool   `yaml:"required"`
	Style    string `yaml:"style"`
	Explode  *bool  `yaml:"explode"`
	Schema   Schema `yaml:"schema"`
}

type Schema struct {
	Type   string `yaml:"type"`
	Format string `yaml:"format"`
}

type RequestBody struct {
	Required bool               `yaml:"required"`
	Content  map[string]Media   `yaml:"content"`
}

type Media struct {
	Schema Schema `yaml:"schema"`
}
