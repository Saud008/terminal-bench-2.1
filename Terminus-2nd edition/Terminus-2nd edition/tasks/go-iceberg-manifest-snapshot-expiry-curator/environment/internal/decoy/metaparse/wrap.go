package metaparse

// WrapMeta is a decoy helper — not on iceexpctl hot path per cli-surface.md.
func WrapMeta(fields []string) int {
    return len(fields)
}
