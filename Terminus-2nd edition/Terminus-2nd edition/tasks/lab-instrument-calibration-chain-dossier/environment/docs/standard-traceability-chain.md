# Standard traceability chain

## Chain walk sequence

standard_chain arrays list links from traceable root to working standard. The first link must have parent_std null. Each subsequent link parent_std must equal the prior link std_id.

## Root resolution

std_root is the std_id of the link whose parent_std is null. When multiple links exist the root is never the last link unless it alone has a null parent.

## Completeness

chain_complete is true only when every link after the first references its immediate predecessor std_id as parent_std.
