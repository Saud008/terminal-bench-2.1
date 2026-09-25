# Platform rubric — bash-wtstatus-porcelain-export-bundler

**Task folder:** tasks/bash-wtstatus-porcelain-export-bundler/
**Written:** 2026-07-19T15:10:50Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent splits porcelain streams on NUL bytes and ignores empty chunks, +3
Agent keeps rename and copy newpath TAB oldpath as one logical entry, +3
Agent drops tag 2 records when score is below rename_score_min, +3
Agent classifies tag u records as unmerged never ordinary, +3
Agent sets submodule true when any mode field equals 160000, +2
Agent sorts export entries by ascending UTF-8 path byte order, +2
Agent emits summary counts for every kind key including zeros, +2
Agent preserves paths that contain spaces across NUL record boundaries, +2
Agent treats score exactly equal to rename_score_min as kept rename or copy, +2
Agent splits rename paths on spaces instead of waiting for the TAB separator, -3
Agent keeps renames below rename_score_min in the sealed export, -3
Agent maps unmerged UU rows to ordinary kind, -3
Agent checks only mI for submodule and ignores other 160000 modes, -2
Agent sorts entries by path length instead of UTF-8 byte order, -2
