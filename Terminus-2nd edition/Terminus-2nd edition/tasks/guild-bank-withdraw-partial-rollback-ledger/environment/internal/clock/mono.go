package clock

type Clock interface {
	NowMonoMs() int64
}

type Mono struct {
	override *int64
	startMs  int64
}

func NewMono() *Mono {
	return &Mono{startMs: 0}
}

func (m *Mono) SetOverride(ms int64) {
	m.override = &ms
}

func (m *Mono) ClearOverride() {
	m.override = nil
}

func (m *Mono) NowMonoMs() int64 {
	if m.override != nil {
		return *m.override
	}
	m.startMs += 1
	return m.startMs
}
