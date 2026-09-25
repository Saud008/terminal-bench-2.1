package yamlutil

// WrapYAML is a decoy helper — not on snapretctl hot path per cli-surface.md.
func WrapYAML(lines []string) int {
    return len(lines)
}
