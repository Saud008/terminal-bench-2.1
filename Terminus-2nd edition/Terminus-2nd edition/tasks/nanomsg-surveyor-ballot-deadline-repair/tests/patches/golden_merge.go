package ballot

import "sort"

type MergeState struct {
	SealedVotes  map[string]int
	PendingVotes map[string]int
	Partial      []string
	Final        map[string]int
	DeadlineHit  bool
}

func NewMergeState() *MergeState {
	return &MergeState{
		SealedVotes:  map[string]int{},
		PendingVotes: map[string]int{},
		Partial:      []string{},
		Final:        map[string]int{},
	}
}

func (m *MergeState) StageVote(respondent string, vote int, sealed bool) {
	if sealed {
		m.SealedVotes[respondent] = vote
		delete(m.PendingVotes, respondent)
		return
	}
	m.PendingVotes[respondent] = vote
}

func (m *MergeState) FinalizeAtDeadline() {
	if m.DeadlineHit {
		return
	}
	m.DeadlineHit = true
	m.Final = map[string]int{}
	m.Partial = []string{}
	for r, v := range m.SealedVotes {
		m.Final[r] = v
	}
	for r := range m.PendingVotes {
		m.Partial = append(m.Partial, r)
	}
	sort.Strings(m.Partial)
}

func (m *MergeState) PartialRespondents() []string {
	return append([]string{}, m.Partial...)
}
