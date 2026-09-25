# Chunk traversal

Chunk indices in the sidecar are stored in row-major order: the last dimension varies fastest when mapping a linear chunk index to multidimensional chunk coordinates.

Given dimension lengths dims and chunk_dims, compute chunks per axis:

    chunks_per_axis[i] = ceil(dims[i] / chunk_dims[i])

Let counts = chunks_per_axis. To decode linear index L into chunk coordinate vector (c0, c1, ...):

    for axis from last down to 0:
        c_axis = L % counts[axis]
        L = L / counts[axis]

The byte origin for the chunk is origin_axis = c_axis * chunk_dims[axis].

The linear decode is used only for consistency checks against origins stored in the index sidecar. Exported lineage always lists the index origin coordinates.
