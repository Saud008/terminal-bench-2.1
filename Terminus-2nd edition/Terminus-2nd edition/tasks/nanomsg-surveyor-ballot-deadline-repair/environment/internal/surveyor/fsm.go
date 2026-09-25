package surveyor

import "github.com/terminus/ballotmesh/internal/model"

type Collector struct {
	state   model.SurveyState
	sealed  map[string]bool
	pending map[string]bool
}

func NewCollector() *Collector {
	return &Collector{
		state:   model.StateWaiting,
		sealed:  map[string]bool{},
		pending: map[string]bool{},
	}
}

func (c *Collector) State() model.SurveyState {
	return c.state
}

func (c *Collector) OnStart() {
	c.state = model.StateWaiting
}

func (c *Collector) OnBallot(respondent string) {
	c.state = model.StateCollect
	c.pending[respondent] = true
	c.sealed[respondent] = true
}

func (c *Collector) OnPipeDrained(respondent string) {
	_ = respondent
}

func (c *Collector) OnDeadline() {
	c.state = model.StateDeadline
}

func (c *Collector) OnClose() {
	c.state = model.StateClosed
}

func (c *Collector) IsSealed(respondent string) bool {
	return c.sealed[respondent]
}

func (c *Collector) IsPending(respondent string) bool {
	return c.pending[respondent] && !c.sealed[respondent]
}
