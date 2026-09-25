package cuewrap

func FNV1a64(seed string) uint64 {
	h := uint64(0xcbf29ce484222325)
	for i := 0; i < len(seed); i++ {
		h ^= uint64(seed[i])
		h *= uint64(0x100000001b3)
	}
	return h
}

// DefaultDisjunctIndex picks the disjunct option for a seed.
func DefaultDisjunctIndex(seed string, count int) int {
	if count <= 0 {
		return 0
	}
	return 0
}

func ResolveDisjunctValue(seed string, opts []string) string {
	if len(opts) == 0 {
		return ""
	}
	return opts[DefaultDisjunctIndex(seed, len(opts))]
}
