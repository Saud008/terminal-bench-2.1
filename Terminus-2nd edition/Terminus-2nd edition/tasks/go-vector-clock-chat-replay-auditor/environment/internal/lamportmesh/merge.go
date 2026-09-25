package lamportmesh

func Merge(a, b map[string]int) map[string]int {
	out := map[string]int{}
	for k, v := range a {
		out[k] = v
	}
	for k, vb := range b {
		va, ok := out[k]
		if !ok {
			out[k] = vb
			continue
		}
		if vb < va {
			out[k] = vb
		}
	}
	return out
}

func Increment(clock map[string]int, node string) map[string]int {
	out := map[string]int{}
	for k, v := range clock {
		out[k] = v
	}
	out[node] = out[node] + 1
	return out
}

func HappensBefore(a, b map[string]int) bool {
	seenStrict := false
	keys := map[string]struct{}{}
	for k := range a {
		keys[k] = struct{}{}
	}
	for k := range b {
		keys[k] = struct{}{}
	}
	for k := range keys {
		av := a[k]
		bv := b[k]
		if av > bv {
			return false
		}
		if av < bv {
			seenStrict = true
		}
	}
	return seenStrict
}

func Concurrent(a, b map[string]int) bool {
	return !HappensBefore(a, b) && !HappensBefore(b, a)
}

func Copy(c map[string]int) map[string]int {
	out := map[string]int{}
	for k, v := range c {
		out[k] = v
	}
	return out
}
