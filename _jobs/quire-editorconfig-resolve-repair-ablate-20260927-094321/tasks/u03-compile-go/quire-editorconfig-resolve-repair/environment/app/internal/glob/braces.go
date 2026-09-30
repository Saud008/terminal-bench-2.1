package glob

// bracesPaired reports whether every '}' in p closes an earlier '{' and the
// counts match. Escaped braces are ignored. Unpaired braces are literal.
func bracesPaired(p []byte) bool {
	open, closed := 0, 0
	for i := 0; i < len(p); i++ {
		if p[i] == '\\' && i+1 < len(p) {
			i++
			continue
		}
		switch p[i] {
		case '{':
			open++
		case '}':
			closed++
		}
		if closed > open {
			return false
		}
	}
	return open == closed
}

// singleBrace looks at the brace group opening at p[i]. It returns the index
// of the closing '}' and true when the group has no top-level comma, i.e. it
// is "{}" , "{word}" or a numeric range. Escaped bytes are skipped.
func singleBrace(p []byte, i int) (int, bool) {
	j := i + 1
	for ; j < len(p) && p[j] != '}'; j++ {
		if p[j] == '\\' && j+1 < len(p) {
			j++
			continue
		}
		if p[j] == ',' {
			return j, false
		}
	}
	if j >= len(p) {
		return j, false
	}
	return j, true
}

// insertByte returns p with c inserted before index i.
func insertByte(p []byte, i int, c byte) []byte {
	p = append(p, 0)
	copy(p[i+1:], p[i:])
	p[i] = c
	return p
}
