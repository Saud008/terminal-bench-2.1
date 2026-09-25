Votes stage as pending when a ballot arrives. Pending votes become sealed when pipe_drained confirms the respondent pipe is empty.

At deadline, FinalTally includes sealed votes only. Pending votes at deadline are listed in partial_respondents and must not appear in final_tally.

Finalize runs on the deadline event and once after all events if deadline was present.
