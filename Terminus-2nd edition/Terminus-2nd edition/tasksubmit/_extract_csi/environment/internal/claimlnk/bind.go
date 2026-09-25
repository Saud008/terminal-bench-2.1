package claimlnk

import "github.com/terminus/snapretctl/internal/model"

func JoinMap(cluster model.ClusterJSON) map[string]model.PVC {
    out := map[string]model.PVC{}
    for _, pvc := range cluster.PVCs {
        out[pvc.Name] = pvc
    }
    return out
}

func SnapshotPVC(cluster model.ClusterJSON, snap model.VolumeSnapshot) (model.PVC, bool) {
    jm := JoinMap(cluster)
    pvc, ok := jm[snap.SourcePVC]
    return pvc, ok
}
