# Catalog format

Each modulefile is a text file with extension .mod or .module under a catalog directory. Lines use @ directives. Comments start with #.

Required directives per module:
- @module NAME — unique module id (may include slash version)
- @priority INTEGER — conflict precedence (higher wins)

Optional directives:
- @family NAME — exclusivity group; only one module per family may remain loaded
- @depends MODULE — comma-separated prerequisites (also accepts @requires as alias)
- @conflict MODULE — comma-separated conflicting module ids
- @prepend VAR VALUE — prepend VALUE to environment variable VAR when module loads
- @append VAR VALUE — append VALUE to environment variable VAR when module loads

Parsing rules:
- Blank lines and comment lines are ignored
- Multiple @depends or @requires lines accumulate
- Module records normalize to a single line starting with module| as described in ingest output

Catalog digest:
- Compute SHA256 over all module records joined by newline
- Records must be sorted lexicographically by module name before hashing
