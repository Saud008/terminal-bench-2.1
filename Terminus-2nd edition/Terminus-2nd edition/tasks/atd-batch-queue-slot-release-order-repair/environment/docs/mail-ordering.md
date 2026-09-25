# mail ordering

When a job finishes with non-zero exit_code, failure mail is logged after the registry record for that job is deleted.

The mail hook notify_before_record_delete returns false in correct builds so registry_delete precedes mail_sent in the timeline.
