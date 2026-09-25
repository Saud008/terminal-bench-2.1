package ikesa

type UIDMap struct {
	inUse map[int]bool
}

func NewUIDMap() *UIDMap {
	return &UIDMap{inUse: map[int]bool{}}
}

func (m *UIDMap) Allocate(uid int) bool {
	if m.inUse[uid] {
		return false
	}
	m.inUse[uid] = true
	return true
}

func (m *UIDMap) OnChildDelete(uid int) {}

func (m *UIDMap) OnIkeDown(uid int) {
	delete(m.inUse, uid)
}

func (m *UIDMap) InUse(uid int) bool {
	return m.inUse[uid]
}
