# Platform rubric — cue-default-disjunction-vet-trace-repair

**Task folder:** tasks/cue-default-disjunction-vet-trace-repair/

Agent implements cuewrap compose that writes eval snapshots before vet or export stage 2 runs, +3
Agent enforces snapshot guard so failed evaluations omit values map on disk, +2
Agent resolves bare disjunct fields with fnv1a64 seed modulo option count in stage 1 only, +3
Agent builds vet default traces with full flattened embed lineage chains, +2
Agent exports optional rule provenance rows with filename line source paths, +2
Agent detects embed cycles and surfaces embed cycle errors without partial values, +2
Agent rejects closed schema unknown fields with closed schema rejects field token format, +3
Agent makes stage 2 vet and export read snapshot values without re-running disjunct selection, +3
Agent recomposes when snapshot binding headers or values disagree with fresh compose, +2
Agent patches only export.go while leaving compose snapshot persistence broken, -3
Agent calls EvaluateWorkspace from vet.go or export.go during stage 2, -3
Agent uses diag_linefmt.go or decoy.go on the vet export hot path, -2
Agent hard-codes disjunct defaults instead of seed hash selection, -3
Agent drops hidden ws-twin fixture coverage under verifier fixtures, -2
