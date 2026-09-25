package clock

import "time"

type Clock interface {
	NowMs() int64
}

type Real struct{}

func (Real) NowMs() int64 {
	return time.Now().UnixMilli()
}

type Fixed struct {
	Now int64
}

func (f Fixed) NowMs() int64 {
	return f.Now
}
