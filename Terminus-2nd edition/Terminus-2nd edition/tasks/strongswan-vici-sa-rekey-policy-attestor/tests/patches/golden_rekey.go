package fsm

type RekeyGate struct {
	pendingDelete map[int]bool
}

func NewRekeyGate() *RekeyGate {
	return &RekeyGate{pendingDelete: map[int]bool{}}
}

func (g *RekeyGate) OnDeleteRequest(reqID int) {
	g.pendingDelete[reqID] = true
}

func (g *RekeyGate) OnDeleteResponse(reqID int) {
	delete(g.pendingDelete, reqID)
}

func (g *RekeyGate) OnRekeyInit() bool {
	return len(g.pendingDelete) == 0
}

func (g *RekeyGate) Pending() int {
	return len(g.pendingDelete)
}
