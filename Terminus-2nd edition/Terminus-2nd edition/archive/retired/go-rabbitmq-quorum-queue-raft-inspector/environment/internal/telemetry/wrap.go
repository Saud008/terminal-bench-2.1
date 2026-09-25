package telemetry

import "time"

type Span struct {
    Name string
    Start time.Time
}

func Begin(name string) Span {
    return Span{Name: name, Start: time.Now()}
}

func (s Span) End() int64 {
    return time.Since(s.Start).Milliseconds()
}
