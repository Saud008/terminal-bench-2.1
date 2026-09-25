# Platform rubric — atd-batch-queue-slot-release-order-repair

**Task folder:** tasks/atd-batch-queue-slot-release-order-repair/

Agent repairs spool.sh letter allocation and spool file naming per at-spool-format contract, +3
Agent repairs slots.sh batch slot hold until spool completion per batch-slots contract, +3
Agent repairs seq.sh atomic .SEQ bump without corrupt partial sequence body, +3
Agent repairs mail.sh so failure mail follows registry_delete in timeline per mail-ordering, +3
Agent repairs atq.sh so pending lines sort by ATQ_EPOCH not file mtime per atq-display, +3
Agent exports replay JSON matching export-schema nested shapes for all bundled scenarios, +3
Agent keeps scheduling math independent of replay seed per export-schema, +2
Agent honors TB3_CLOCK_EPOCH override when set instead of --clock, +2
Agent passes hidden slot retry trap with letter advance past occupied spool, +2
Agent passes crash mid-seq fixture with atomic seq bump to expected seq_final, +2
Agent runs reset-state.sh before local replay checks, +1
Agent emits mail_log entries with job and exit_code only without extra epoch field, +2
Agent logs failure mail after registry record deletion on non-zero exit jobs, -3
Agent releases batch slot before spool job completes on multi-job batch, -3
Agent sorts atq_lines by file modification time instead of header ATQ_EPOCH, -3
Agent includes epoch or other extra keys in mail_log export entries, -3
