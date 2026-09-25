package model

type Variant struct {
	MediaType string `json:"media_type"`
	Charset   string `json:"charset"`
	Language  string `json:"language"`
	Body      string `json:"body"`
}

type Resource struct {
	Variants []Variant `json:"variants"`
}

type Catalog struct {
	Resources map[string]Resource `json:"resources"`
}

type CacheStats struct {
	Hits   int `json:"hits"`
	Misses int `json:"misses"`
}

type NegotiationInput struct {
	Accept         string `json:"Accept"`
	AcceptLanguage string `json:"Accept-Language"`
	AcceptCharset  string `json:"Accept-Charset"`
}

type SelectedVariant struct {
	Variant   Variant
	MediaType string
	Charset   string
	Language  string
}
