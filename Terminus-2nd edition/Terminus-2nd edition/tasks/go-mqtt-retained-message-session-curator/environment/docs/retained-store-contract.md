# Retained store contract

Only PUBLISH events with retain true affect the retained store. Latest timestamp wins on overwrite per topic. Empty payload with retain true deletes the retained entry for that topic.
