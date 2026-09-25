# PVC join contract

VolumeSnapshot joins to PersistentVolumeClaim by matching snapshot.namespace plus snapshot.source_pvc to pvc.namespace plus pvc.name.

Join map keys are namespace/name composite, not name alone.
