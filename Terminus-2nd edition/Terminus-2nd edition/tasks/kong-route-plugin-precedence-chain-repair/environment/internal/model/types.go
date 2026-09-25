package model

type Deck struct {
	Services  []Service  `yaml:"services"`
	Routes    []Route    `yaml:"routes"`
	Consumers []Consumer `yaml:"consumers"`
}

type Service struct {
	Name    string   `yaml:"name"`
	URL     string   `yaml:"url"`
	Plugins []Plugin `yaml:"plugins"`
}

type Route struct {
	Name      string   `yaml:"name"`
	Service   string   `yaml:"service"`
	Paths     []string `yaml:"paths"`
	Methods   []string `yaml:"methods"`
	Plugins   []Plugin `yaml:"plugins"`
	Tags      []string `yaml:"tags"`
	ScopeTags []string `yaml:"scope_tags"`
}

type Consumer struct {
	Username string     `yaml:"username"`
	JWT      ConsumerJWT `yaml:"jwt"`
}

type ConsumerJWT struct {
	Key    string   `yaml:"key"`
	Scopes []string `yaml:"scopes"`
}

type Plugin struct {
	Name   string         `yaml:"name"`
	Config map[string]any `yaml:"config"`
}

type MatchRequest struct {
	Method string
	Path   string
}

type MatchResult struct {
	Route   Route
	Service Service
}

type IngestReport struct {
	OK           bool     `json:"ok"`
	RoutesLoaded int      `json:"routes_loaded"`
	Errors       []string `json:"errors,omitempty"`
}

type OpenAPISpec struct {
	OpenAPI    string                 `json:"openapi"`
	Info       map[string]string      `json:"info"`
	Paths      map[string]any         `json:"paths"`
	Components map[string]any         `json:"components,omitempty"`
}

type RateState struct {
	Counts map[string]int
	Limit  int
}
