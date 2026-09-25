# Dialog branch join

Branch key equals call_id plus pipe plus from_tag plus pipe plus to_tag when to_tag present, else call_id pipe from_tag.

Forked dialogs share call_id but differ by to_tag. compile-dialogs must track each branch independently.
