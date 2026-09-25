# Stage ordering contract

A consumer job stage index must be strictly greater than the producer stage index for every required need edge. Optional needs skip stage ordering enforcement. Equal stage indices are allowed for required needs within the same stage DAG.
