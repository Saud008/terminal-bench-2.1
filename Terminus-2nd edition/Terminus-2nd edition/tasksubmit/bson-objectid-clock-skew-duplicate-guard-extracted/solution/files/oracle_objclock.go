package objclock

import (
	"sync"
)

type Generator struct {
	mu       sync.Mutex
	machine  [5]byte
	lastTS   uint32
	counter  uint32
	clockKey string
}

func NewGenerator(machineID string) *Generator {
	g := &Generator{clockKey: machineID}
	g.BindMachine(machineID)
	return g
}

func (g *Generator) BindMachine(machineID string) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.machine = hashMachine(machineID)
	g.clockKey = machineID
}

func (g *Generator) Generate(nowUnix int64) (ID, error) {
	g.mu.Lock()
	defer g.mu.Unlock()
	ts := uint32(nowUnix)
	if ts < g.lastTS {
		return ID{}, ErrMonoReverse
	}
	if ts > g.lastTS {
		g.lastTS = ts
		g.counter = 0
	} else {
		g.counter++
		if g.counter > 0xFFFFFF {
			return ID{}, ErrCounterExhaust
		}
	}
	id := compose(ts, g.machine, g.counter)
	return id, nil
}

func (g *Generator) LastTimestamp() uint32 {
	g.mu.Lock()
	defer g.mu.Unlock()
	return g.lastTS
}
