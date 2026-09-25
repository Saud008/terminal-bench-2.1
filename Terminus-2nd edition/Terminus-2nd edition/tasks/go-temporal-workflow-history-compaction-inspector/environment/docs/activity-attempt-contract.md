# Activity attempt contract

ActivityTaskScheduled carries attempt when explicitly set. Otherwise the tracker increments per activity_id within a run generation. WorkflowExecutionContinuedAsNew resets attempt counters for the next run generation. The continue-as-new fixture uses activity_id rollup across generations.
