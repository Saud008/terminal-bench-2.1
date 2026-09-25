# Intake urgency index formula

urgency_score equals float(1000 minus intake_rank) multiplied by (1.0 minus surrender_prob) plus hold_precedence times 0.01 where hold_precedence comes from adoption hold lookup with default 50.
