package com.flinkskew.util;

import com.flinkskew.align.BarrierAligner;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.FieldNamingPolicy;
import com.google.gson.GsonBuilder;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Map;
import java.util.TreeMap;

public final class BufferDigest {
    private static final Gson CANON = new GsonBuilder().create();

    private BufferDigest() {}

    public static String digest(BarrierAligner.BufferRow row) {
        Map<String, Object> body = new TreeMap<>();
        body.put("alignment_class", row.alignmentClass());
        body.put("attempt_id", row.attemptId());
        body.put("barriers_received", row.barriersReceived());
        body.put("checkpoint_id", row.checkpointId());
        body.put("expected_subtasks", row.expectedSubtasks());
        body.put("first_barrier_ms", row.firstBarrierMs());
        body.put("last_barrier_ms", row.lastBarrierMs());
        body.put("operator_id", row.operatorId());
        body.put("skew_ms", row.skewMs());
        String raw = CANON.toJson(body);
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(raw.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 8; i++) {
                sb.append(String.format("%02x", hash[i]));
            }
            return sb.toString();
        } catch (Exception ex) {
            throw new RuntimeException(ex);
        }
    }
}
