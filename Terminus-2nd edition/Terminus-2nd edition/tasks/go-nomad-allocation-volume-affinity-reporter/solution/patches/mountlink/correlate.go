package mountlink

import (
	"os"
	"sort"

	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"
)

func namespaceSalt() string {
	return os.Getenv("TB3_NAMESPACE_SALT")
}

func volumeKey(vol model.CSIVolume) string {
	key := vol.Namespace + "/" + vol.VolumeID
	if s := namespaceSalt(); s != "" {
		key = key + s
	}
	return key
}

func JoinMounts(allocs []model.ScopedAllocation, volumes []model.CSIVolume) []model.VolumeJoinRow {
	volByID := map[string]model.CSIVolume{}
	for _, v := range volumes {
		volByID[v.VolumeID] = v
	}
	rows := make([]model.VolumeJoinRow, 0)
	for _, a := range allocs {
		for _, m := range a.CSIMounts {
			vol, ok := volByID[m.VolumeID]
			key := m.VolumeID
			plugin := ""
			joinOK := false
			if ok {
				key = volumeKey(vol)
				plugin = vol.PluginID
				joinOK = true
			}
			rows = append(rows, model.VolumeJoinRow{
				AllocID:   a.AllocID,
				VolumeKey: key,
				PluginID:  plugin,
				MountPath: m.MountPath,
				ReadOnly:  m.ReadOnly,
				JoinOK:    joinOK,
			})
		}
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].AllocID != rows[j].AllocID {
			return rows[i].AllocID < rows[j].AllocID
		}
		return rows[i].VolumeKey < rows[j].VolumeKey
	})
	return rows
}
