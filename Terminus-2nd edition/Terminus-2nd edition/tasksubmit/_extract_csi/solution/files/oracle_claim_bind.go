package claimlnk

import "github.com/terminus/snapretctl/internal/model"

func pvcKey(namespace, name string) string {
    return namespace + "/" + name
}

func JoinMap(cluster model.ClusterJSON) map[string]model.PVC {
    out := map[string]model.PVC{}
    for _, pvc := range cluster.PVCs {
        out[pvcKey(pvc.Namespace, pvc.Name)] = pvc
    }
    return out
}

func SnapshotPVC(cluster model.ClusterJSON, snap model.VolumeSnapshot) (model.PVC, bool) {
    jm := JoinMap(cluster)
    pvc, ok := jm[pvcKey(snap.Namespace, snap.SourcePVC)]
    return pvc, ok
}
