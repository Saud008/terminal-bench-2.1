# NEVRA lineage order

Package rows extracted from primary.xml must include name, epoch, version, release, arch, and a nevra key string.

The nevra key format is epoch:name-version-release.arch where epoch is always present as a decimal integer prefix before the colon, including epoch zero.

Within each name and arch group, assign lineage_rank starting at 1 for the newest EVRA and increasing for older packages. Newest means greatest epoch, then greatest version by RPM version segment comparison, then greatest release by the same segment rules. Never rank using plain ASCII sort on the version field alone.

Example: epoch 1 version 2.10 outranks epoch 0 version 2.9 even when 2.9 sorts higher as a string.
