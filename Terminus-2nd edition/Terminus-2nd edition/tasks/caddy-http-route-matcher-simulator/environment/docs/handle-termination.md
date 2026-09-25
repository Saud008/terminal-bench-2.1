# Handle termination

Routes belong to a named group string from ingest. Matcher evaluation scopes to one group at a time based on the first matching candidate group.

When a matching route has terminal set to true, no further routes in that group may win, including handle_path routes listed later in the array.

handle_path routes are path-only handlers within a group. They must not be selected after a terminal route in the same group has already matched the request.

Terminal false routes may still lose to a higher specificity sibling in the same group per the specificity document.

Cross-group routes are not considered once a group winner is chosen.
