# Match branch join

Branch key equals duel_id plus pipe plus lane_tag plus pipe plus fork_tag when fork_tag present, else duel_id pipe lane_tag.

Forked matches share duel_id but differ by fork_tag. fold-branches must track each branch independently.
