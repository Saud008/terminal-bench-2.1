# Policy constraints

policy.json lists forbidden_if_set, required_n, and max_modular symbol lists.

forbidden_if_set: symbol must not be y or m.

required_n: symbol must be n or absent.

max_modular: symbol must not be y; m or n is allowed.

Violations are sorted by symbol name. Codes are forbidden_set, required_n, and max_modular.

Policy scan runs on after_deps symbols from the stage snapshot.
