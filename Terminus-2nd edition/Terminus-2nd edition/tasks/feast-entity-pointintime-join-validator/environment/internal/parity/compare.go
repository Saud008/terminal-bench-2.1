package parity

import (
	"fmt"
	"math"
)

func ValuesMatch(a, b float64) bool {
	return fmt.Sprintf("%v", a) == fmt.Sprintf("%v", b)
}

func Round3(v float64) float64 {
	return math.Round(v*1000) / 1000
}
