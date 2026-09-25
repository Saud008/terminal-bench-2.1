# Folder filter rules

Each non-empty, non-comment line is:

    include GLOB
    exclude GLOB

Globs use fnmatch semantics on the full folder name (case sensitive).

Evaluation order for folders listed in imap-meta:

1. Drop any folder matching an exclude glob.
2. If at least one include rule exists, keep only folders matching any include glob.
3. If no include rules exist, keep all non-excluded folders.

Folder filtering must run before maxage selection and before the staging snapshot lists active folders. Applying include/exclude after message selection is invalid.
