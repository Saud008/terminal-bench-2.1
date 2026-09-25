# DST gap handling

During a daylight-saving spring-forward gap, wall times that do not exist must not produce extra fires. Only valid instants returned by the cron schedule in the job location may appear in planned_fires and in execution rows.

Boundary fixtures include America/New_York spring-forward windows; duplicate gap-hour fires are incorrect.
