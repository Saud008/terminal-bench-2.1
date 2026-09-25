# Path regexp anchors

path_regexp patterns in staging are full-path patterns. Each pattern must compile as a regular expression anchored to the entire request path.

Implicit anchors are required even when the JSON pattern omits caret and dollar. A pattern written as /admin must only match the path /admin, not /prefix/admin or /admin/suffix.

Do not use substring containment checks. Use regular expression compilation with start and end anchors on the request path string.

Wildcards in path (non-regexp) matchers are separate from path_regexp and follow prefix rules in the specificity document.
