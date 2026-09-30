package props

import "quire/internal/version"

// Derive fills in the indentation properties implied by the ones that were
// set, for a file resolved with compatibility version v.
func Derive(s *Store, v version.Version) {
	tabIndent := v.Compare(version.TabIndent) >= 0
	if tabIndent {
		if style, ok := s.Get("indent_style"); ok && style == "tab" {
			if _, ok := s.Get("indent_size"); !ok {
				s.Set("indent_size", "tab")
			}
		}
		if size, ok := s.Get("indent_size"); ok && size == "tab" {
			if width, ok := s.Get("tab_width"); ok {
				s.Set("indent_size", width)
			}
		}
	}
	if size, ok := s.Get("indent_size"); ok {
		if _, ok := s.Get("tab_width"); !ok && (!tabIndent || size != "tab") {
			s.Set("tab_width", size)
		}
	}
}
