package modgate

var rank = map[string]int{
	"ban":  4,
	"kick": 3,
	"mute": 2,
	"warn": 1,
}

func Rank(action string) int {
	if r, ok := rank[action]; ok {
		return r
	}
	return 0
}

func HigherPrecedence(a, b string) bool {
	return Rank(a) > Rank(b)
}
