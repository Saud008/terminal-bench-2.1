package com.flinkskew.emit;

import com.flinkskew.align.BarrierAligner;
import com.flinkskew.util.JsonUtil;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.FieldNamingPolicy;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class ChronicleWriter {
    private static final Gson GSON = new GsonBuilder()
            .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
            .create();

    private ChronicleWriter() {}

    public record OperatorRow(
            String operatorId,
            int skewMs,
            String alignmentClass,
            String misalignmentClass,
            int barriersReceived,
            int expectedSubtasks
    ) {}

    public record CheckpointBlock(int checkpointId, int attemptId, List<OperatorRow> operators, Map<String, Object> summary) {}

    public record Chronicle(String jobId, int alignmentTimeoutMs, List<CheckpointBlock> checkpoints) {}

    public static void emit(Path bufferPath, Path outPath) throws IOException {
        Map<String, Object> jobMeta = JsonUtil.readMap(Path.of("/app/fixtures/config/job_meta.json"));
        String jobId = (String) jobMeta.get("job_id");
        int timeout = ((Number) jobMeta.get("alignment_timeout_ms")).intValue();
        List<String> lines = Files.readAllLines(bufferPath, StandardCharsets.UTF_8);
        Map<String, List<BarrierAligner.BufferRow>> grouped = new HashMap<>();
        for (String line : lines) {
            if (line.isBlank()) {
                continue;
            }
            BarrierAligner.BufferRow row = GSON.fromJson(line, BarrierAligner.BufferRow.class);
            String key = row.checkpointId() + "|" + row.attemptId();
            grouped.computeIfAbsent(key, k -> new ArrayList<>()).add(row);
        }
        List<CheckpointBlock> checkpoints = new ArrayList<>();
        for (Map.Entry<String, List<BarrierAligner.BufferRow>> entry : grouped.entrySet()) {
            String[] parts = entry.getKey().split("\\|");
            int cp = Integer.parseInt(parts[0]);
            int attempt = Integer.parseInt(parts[1]);
            List<OperatorRow> ops = new ArrayList<>();
            int maxSkew = 0;
            int timeoutCount = 0;
            int unalignedCount = 0;
            for (BarrierAligner.BufferRow row : entry.getValue()) {
                maxSkew = Math.max(maxSkew, row.skewMs());
                if ("TIMEOUT_VIOLATION".equals(row.alignmentClass())) {
                    timeoutCount++;
                }
                if ("UNALIGNED_DECLARED".equals(row.alignmentClass())) {
                    unalignedCount++;
                }
                String mis = "TIMEOUT_VIOLATION".equals(row.alignmentClass()) ? "SKEW_TIMEOUT" : row.alignmentClass();
                ops.add(new OperatorRow(row.operatorId(), row.skewMs(), row.alignmentClass(), mis,
                        row.barriersReceived(), row.expectedSubtasks()));
            }
            ops.sort(Comparator.comparing(OperatorRow::operatorId));
            Map<String, Object> summary = new HashMap<>();
            summary.put("operator_count", ops.size());
            summary.put("max_skew_ms", maxSkew);
            summary.put("timeout_violation_count", timeoutCount);
            summary.put("unaligned_count", unalignedCount);
            checkpoints.add(new CheckpointBlock(cp, attempt, ops, summary));
        }
        checkpoints.sort(Comparator.comparingInt(CheckpointBlock::checkpointId)
                .thenComparingInt(CheckpointBlock::attemptId));
        JsonUtil.writePretty(outPath, new Chronicle(jobId, timeout, checkpoints));
    }
}
