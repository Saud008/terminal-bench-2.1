package com.flinkskew.model;

import com.google.gson.annotations.SerializedName;

public final class EventRecord {
    @SerializedName("event_kind")
    public String eventKind;
    @SerializedName("checkpoint_id")
    public int checkpointId;
    @SerializedName("attempt_id")
    public int attemptId;
    @SerializedName("operator_id")
    public String operatorId;
    @SerializedName("subtask_index")
    public int subtaskIndex;
    @SerializedName("timestamp_ms")
    public long timestampMs;
    @SerializedName("is_unaligned")
    public boolean isUnaligned;
    @SerializedName("aligned_checkpoint_timeout_ms")
    public int alignedCheckpointTimeoutMs;
}
