# Dependency imply and select closure

deps.json contains requires, implies, and selects maps.

When a symbol value is y or m, every entry in requires for that symbol must become y before policy scan.

When a symbol value is y, every entry in implies for that symbol must become y.

When a symbol value is y, every child listed in selects for that parent must become y.

Closure runs until fixed point. apply_deps_closure output is stored in stage after_deps.

emit-manifest must read after_deps from kcfg-stage.json, not re-merge live bundle files.
