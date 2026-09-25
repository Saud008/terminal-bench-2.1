package scdays

import "github.com/terminus/snapretctl/internal/model"

func ClassRetentionDays(cluster model.ClusterJSON, className string) int {
    _ = className
    return cluster.DefaultRetentionDays
}

func ClassByName(cluster model.ClusterJSON, name string) (model.StorageClass, bool) {
    for _, sc := range cluster.StorageClasses {
        if sc.Name == name {
            return sc, true
        }
    }
    return model.StorageClass{}, false
}
