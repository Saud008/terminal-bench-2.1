package thread

import (
	"sort"

	"mailindex/internal/model"
)

func PickThreadRoots(components map[string][]model.MailMessage) map[string]string {
	rootForComponent := map[string]string{}
	for compKey, members := range components {
		sort.Slice(members, func(i, j int) bool {
			if members[i].DateUnix == members[j].DateUnix {
				return members[i].MessageID < members[j].MessageID
			}
			return members[i].DateUnix < members[j].DateUnix
		})
		rootForComponent[compKey] = members[0].MessageID
	}
	return rootForComponent
}
