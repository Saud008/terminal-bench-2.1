# Input compensation buffer

Client inputs are queued until the server acknowledges them. Compensation delay in ticks is:

delay_ticks = (lag_estimate_us * tick_rate_hz) / 1_000_000

Apply compensation only for inputs whose input_seq has received an input_ack event before apply_compensation runs. Inputs still waiting for ack must not increment buffered_inputs_applied.

Tick rate defaults to 60 Hz when not passed on the CLI; TB3_TICK_RATE_HZ may override when simulate --tick-rate is zero.
