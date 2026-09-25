# Filter rule language

Rules are line based. Prefix - means exclude, + means include, P means protect from delete, and R marks delete risk for receiver-only files.
Pattern matching uses fnmatch shell style globs for path rules. A pattern beginning with / is anchored at the root of the transfer tree.
