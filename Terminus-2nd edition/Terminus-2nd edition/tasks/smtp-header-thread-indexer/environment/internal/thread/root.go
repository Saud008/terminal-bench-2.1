package thread

import (
	"sort"

	"mailindex/internal/model"
)

// PickThreadRoots selects the root Message-ID per connected component.
// Broken: picks the latest message instead of the earliest.
func PickThreadRoots(components map[string][]model.MailMessage) map[string]string {
	rootForComponent := map[string]string{}
	for compKey, members := range components {
		sort.Slice(members, func(i, j int) bool {
			if members[i].DateUnix == members[j].DateUnix {
				return members[i].MessageID < members[j].MessageID
			}
			return members[i].DateUnix < members[j].DateUnix
		})
		rootForComponent[compKey] = members[len(members)-1].MessageID
	}
	return rootForComponent
}
