Surveyor states: waiting, collecting, deadline, closed.

start moves to waiting. ballot moves to collecting. deadline moves to deadline. close moves to closed.

A ballot is sealed only after the matching pipe_drained event for the same respondent arrives later in the timeline. TallyIncluded on ballot events must remain false until that drain event.

pipe_drained after a ballot seals the pending ballot for that respondent if a vote was staged.
