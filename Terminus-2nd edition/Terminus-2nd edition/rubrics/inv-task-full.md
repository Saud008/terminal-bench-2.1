# Platform rubric — inv-task-full

**Task folder:** tasks/inv-task-full/

Agent implements inv-vault-audit scan staging with host-rows.ndjson exposure-rows.ndjson and scan-manifest.json digest, +3
Agent expands inventory group children before direct host sections for lineage merge order, +2
Agent orders group_vars from parent to child so child layer vars override parent values, +3
Agent applies host_vars after all group_vars layers per vars-precedence contract, +2
Agent detects vault markers with whitespace trimming on ANSIBLE_VAULT lines and YAML vault blocks, +2
Agent honors inventory-ignore and ansible.cfg ignore_patterns without merging ignored vars into hosts, +3
Agent computes staging_digest from host-rows.ndjson and exposure-rows.ndjson combined bytes, +2
Agent implements emit that reads scan artifacts only without reopening inventory tree paths, +3
Agent emits vault-exposure-report.json with vault_exposure plaintext_secret and precedence_shadow findings, +3
Agent preserves run_seq stability when re-scanning an unchanged tree fingerprint, +2
Agent increments run_seq when scanning a new tree fingerprint, +1
Agent sorts findings by category host and var_key in emit output, +1
Agent wires inventory_engine.py with rebuild in test.sh, +2
Agent fixes only emit while leaving scan precedence or ignore filters broken, -3
Agent patches decoy ansible-vault-decrypt.sh or wrap legacy-inventory-merge.sh on the hot path, -3
Agent re-reads inventory hosts.ini or group_vars during emit after scan, -5
Agent drops TB3 nested-vault or ignore-bypass hidden tree coverage, -2
Agent weakens staging digest to host-rows.ndjson only excluding exposure findings, -3
