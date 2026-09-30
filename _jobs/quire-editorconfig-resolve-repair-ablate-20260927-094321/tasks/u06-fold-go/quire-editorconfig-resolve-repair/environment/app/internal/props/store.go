// Package props keeps the properties collected for one file.
package props

import "quire/internal/ctext"

// Pair is one property as printed.
type Pair struct {
	Name, Value string
}

// Store is an ordered set of properties keyed by lowercased name.
type Store struct {
	pairs []Pair
}

// Set records a property. Names are case-insensitive and stored lowercased;
// values of the properties listed in folded are lowercased too. The last
// value set for a name wins.
func (s *Store) Set(name, value string) {
	name = ctext.Lower(name)
	value = foldValue(name, value)
	for i := range s.pairs {
		if s.pairs[i].Name == name {
			s.pairs = append(s.pairs[:i], s.pairs[i+1:]...)
			break
		}
	}
	s.pairs = append(s.pairs, Pair{name, value})
}

// Get returns the value stored for a lowercased name.
func (s *Store) Get(name string) (string, bool) {
	for _, p := range s.pairs {
		if p.Name == name {
			return p.Value, true
		}
	}
	return "", false
}

// Reset forgets every property.
func (s *Store) Reset() {
	s.pairs = nil
}

// Pairs returns the properties in output order.
func (s *Store) Pairs() []Pair {
	return s.pairs
}
