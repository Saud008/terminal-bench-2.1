# Platform rubric — hashicorp-hcl2-attr-block-composer

**Task folder:** tasks/hashicorp-hcl2-attr-block-composer/

Agent deep-merges nested attribute objects across fragments instead of shallow replacement, +3
Agent applies merge_override maps before dynamic block expansion, +3
Agent treats explicit null in merge_override as removing the target key, +3
Agent exports block labels using lowest source-order fragment without alphabetizing, +2
Agent derives merge-checksum.txt from sorted normalized JSON not pretty HCL text, +3
Agent writes /app/state/hcl-stage.json with fragment order dynamics and merge_overrides, +2
Agent rebuilds /app/bin/hclctl in test.sh after editing internal merge or export code, +2
Agent reads staging snapshot in merge export rather than re-parsing fragment files, +2
Agent leaves internal/decoy off the export hot path, +1
Agent patches only shallow merge while leaving null override semantics broken, -3
Agent expands dynamic blocks before applying merge_override attributes, -3
Agent hashes pretty-printed merged.hcl for the export checksum, -3
Agent sorts repeated block label keys alphabetically on export, -2
