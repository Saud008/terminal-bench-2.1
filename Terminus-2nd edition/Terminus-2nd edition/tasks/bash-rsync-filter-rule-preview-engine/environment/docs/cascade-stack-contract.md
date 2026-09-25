# Cascade stack

Root rules apply first. For a path under nested directories, each ancestor directory may contribute .rsync-filter rows.
Ancestor cascade overlay files append in top-down order. cascade_depth counts the root layer plus each ancestor layer considered.
rule_cascade records the exact directories that contributed rules for each path.
