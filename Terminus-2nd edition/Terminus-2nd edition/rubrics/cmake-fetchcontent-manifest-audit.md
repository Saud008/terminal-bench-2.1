# Platform rubric — cmake-fetchcontent-manifest-audit

**Task folder:** tasks/cmake-fetchcontent-manifest-audit/

# Rubric 1

Agent implements ingest snapshot staging before cmake-tree export, +3
Agent resolves add_subdirectory paths relative to list file directory, +3
Agent collects FetchContent metadata in declaration order, +2
Agent aborts parse with exit 2 on malformed lists before output, +2
Agent patches ingest.sh only leaving export_tree broken, -3
Agent writes cmake-tree.json without ingest snapshot file, -2
Agent uses root CMakeLists fetchcontent only ignoring nested lists, -2

# Rubric 2

Agent hashes compressed tar.gz bytes for URL_HASH audit, +3
Agent reads PIN overlay git commit fields for hash audit, +2
Agent writes hash-audit-snapshot.json before hash-audit JSON, +3
Agent flags tarball digest mismatch in failures array, +2
Agent hardcodes vendor digest instead of reading archive bytes, -3
Agent skips hash snapshot write on successful audit, -2
Agent compares unpacked tree hash instead of tarball SHA256, -2

# Rubric 3

Agent unions FetchContent names from every parsed tree file, +3
Agent gates scan on empty failures in hash audit snapshot, +3
Agent walks install prefix recording symlink kind with dash sha256, +2
Agent includes libbaz in transitive_closure from nested lists, +2
Agent patches fetch_closure only leaving scan on broken closure, -3
Agent skips hash snapshot gate during install manifest scan, -2
Agent reports direct deps only omitting nested FetchContent, -2
