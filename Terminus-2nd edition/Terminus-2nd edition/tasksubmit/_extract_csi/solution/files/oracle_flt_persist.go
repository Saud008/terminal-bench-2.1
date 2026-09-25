package fltstore

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/snapretctl/internal/model"
)

const DefaultStagePath = "/app/state/k8s-fleet-graph.json"

func WriteFleetGraph(path string, snap model.FleetGraphFile) error {
	if path == "" {
		path = DefaultStagePath
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	digest, err := computeDigest(snap.Cluster)
	if err != nil {
		return err
	}
	snap.FleetGraphDigest = digest
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func ReadFleetGraph(path string) (model.FleetGraphFile, error) {
	if path == "" {
		path = DefaultStagePath
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.FleetGraphFile{}, err
	}
	var snap model.FleetGraphFile
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.FleetGraphFile{}, err
	}
	return snap, nil
}

func computeDigest(cluster model.ClusterJSON) (string, error) {
	sortedSnaps := make([]model.VolumeSnapshot, len(cluster.Snapshots))
	copy(sortedSnaps, cluster.Snapshots)
	sort.Slice(sortedSnaps, func(i, j int) bool { return sortedSnaps[i].UID < sortedSnaps[j].UID })
	sortedPVCs := make([]model.PVC, len(cluster.PVCs))
	copy(sortedPVCs, cluster.PVCs)
	sort.Slice(sortedPVCs, func(i, j int) bool {
		if sortedPVCs[i].Namespace != sortedPVCs[j].Namespace {
			return sortedPVCs[i].Namespace < sortedPVCs[j].Namespace
		}
		return sortedPVCs[i].Name < sortedPVCs[j].Name
	})
	clusterCopy := cluster
	clusterCopy.Snapshots = sortedSnaps
	clusterCopy.PVCs = sortedPVCs
	payload := map[string]any{"cluster": clusterCopy}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:]), nil
}
