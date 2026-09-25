# Namespace aliasing

Record schemas may declare aliases as fully qualified prior names. When comparing writer and reader record names, resolve alias tables **before** comparing bare names.

A reader alias entry com.legacy.User matches a writer whose full name is com.example.events.User when the reader declares that alias and the simple name User matches.

Alias equivalence must not require identical namespace strings when an alias bridge exists on either side.
