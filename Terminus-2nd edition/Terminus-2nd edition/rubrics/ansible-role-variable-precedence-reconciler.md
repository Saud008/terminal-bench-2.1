# Platform rubric — ansible-role-variable-precedence-reconciler

**Task folder:** tasks/ansible-role-variable-precedence-reconciler/

# Rubric 1

Agent merges group_vars/all.yml before named group files in ascending group name order, +3
Agent applies host_vars after all group_vars for the target host, +3
Agent collects direct inventory group membership from hosts.ini without children expansion mistakes, +2
Agent writes resolve output JSON with host seed and merged keys, +2
Agent merges host_vars before group_vars layers, -3

# Rubric 2

Agent applies role defaults before inventory group and host vars, +3
Agent applies role vars after inventory layers so vars override inventory, +3
Agent merges role defaults before role vars within each role, +3
Agent lets inventory override colliding role default worker_pool keys, +2
Agent merges inventory before role defaults on colliding keys, -3

# Rubric 3

Agent honors hash_behaviour merge for nested dict collisions, +3
Agent sorts include_vars by ascending depth not lexical path, +3
Agent applies playbook vars before extra vars in final stack, +3
Agent preserves sibling cache keys under hash merge when host ttl updates, +2
Agent merges extra vars before playbook vars, -3
