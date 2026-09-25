package fsm

// RekeyGate tracks pending CHILD_SA delete acknowledgements before rekey.
type RekeyGate struct {
	pendingDelete map[int]bool
	rekeyAllowed  bool
}

func NewRekeyGate() *RekeyGate {
	return &RekeyGate{pendingDelete: map[int]bool{}}
}

func (g *RekeyGate) OnDeleteRequest(reqID int) {
	g.pendingDelete[reqID] = true
	g.rekeyAllowed = true
}

func (g *RekeyGate) OnDeleteResponse(reqID int) {
	delete(g.pendingDelete, reqID)
}

func (g *RekeyGate) OnRekeyInit() bool {
	if len(g.pendingDelete) > 0 && g.rekeyAllowed {
		return true
	}
	return len(g.pendingDelete) == 0
}

func (g *RekeyGate) Pending() int {
	return len(g.pendingDelete)
}
