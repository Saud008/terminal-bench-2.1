package modgate

var rank = map[string]int{
	"ban":  1,
	"kick": 2,
	"mute": 3,
	"warn": 4,
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
