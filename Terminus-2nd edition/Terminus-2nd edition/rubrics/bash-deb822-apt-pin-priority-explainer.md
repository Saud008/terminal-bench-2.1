# Platform rubric — bash-deb822-apt-pin-priority-explainer

**Task folder:** tasks/bash-deb822-apt-pin-priority-explainer/

Agent implements debpol build-policy writing deb822-policy-graph.json with origins and package_rows, +3
Agent parses deb822 continuation lines into multi-value URIs fields, +3
Agent ranks origins by Default-Pin descending before collecting index rows, +2
Agent matches Pin version globs against upstream after stripping epoch prefix, +3
Agent compares dpkg versions with epoch upstream revision and tilde ordering, +3
Agent rejects package rows with missing arch when target arch is set, +2
Agent computes graph_digest from origin_fingerprint and sorted package tuples, +2
Agent selects install candidates by highest effective_priority then newer version, +3
Agent sorts install_candidates by package name in candidate-report export, +2
Agent reads deb822-policy-graph.json only during candidate-report not ingest work, +2
Agent honors TB3_SCENARIO_ROOT overlay for hidden tb3-pin-trap scenario bundles, +2
Agent patches release_label_sort decoy on build or report hot path, -3
Agent fixes origin rank only while export tie-break still keeps first row, -3
Agent treats missing arch as universal match during candidate selection, -5
Agent drops tilde glob pin matching for hidden widget prerelease trap, -3
Agent weakens graph_digest by omitting origin_fingerprint from digest input, -2
