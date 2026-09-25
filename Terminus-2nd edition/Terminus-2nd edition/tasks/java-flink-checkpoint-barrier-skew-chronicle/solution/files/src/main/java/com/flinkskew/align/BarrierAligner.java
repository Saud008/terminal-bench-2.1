package com.flinkskew.align;

import com.flinkskew.chain.ChainedOperatorBoundary;
import com.flinkskew.map.SubtaskOperatorMapper;
import com.flinkskew.model.EventRecord;
import com.flinkskew.util.BufferDigest;
import com.flinkskew.watermark.WatermarkGuard;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.FieldNamingPolicy;
import com.google.gson.reflect.TypeToken;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class BarrierAligner {
    private static final Gson GSON = new GsonBuilder()
            .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
            .create();
    private static final int DEFAULT_TIMEOUT = 60000;

    private BarrierAligner() {}

    public record BufferRow(
            int checkpointId,
            int attemptId,
            String operatorId,
            int skewMs,
            String alignmentClass,
            int barriersReceived,
            int expectedSubtasks,
            long firstBarrierMs,
            long lastBarrierMs,
            String bufferDigest
    ) {}

    public static void align(Path indexPath, Path outPath) throws IOException {
        String raw = Files.readString(indexPath, StandardCharsets.UTF_8);
        List<EventRecord> events = GSON.fromJson(raw, new TypeToken<List<EventRecord>>() {}.getType());
        SubtaskOperatorMapper.Graph graph = SubtaskOperatorMapper.loadGraph(Path.of("/app/fixtures/config"));
        Map<String, List<Long>> buckets = new HashMap<>();
        Map<String, Boolean> unalignedFlags = new HashMap<>();
        Map<String, Integer> timeouts = new HashMap<>();
        for (EventRecord ev : events) {
            if (!WatermarkGuard.countsAsBarrierReceipt(ev)) {
                continue;
            }
            String mapped = SubtaskOperatorMapper.mapOperator(ev, graph);
            if (!ChainedOperatorBoundary.acceptReceipt(ev, mapped, graph)) {
                continue;
            }
            String gkey = ev.checkpointId + "|" + ev.attemptId + "|" + mapped;
            unalignedFlags.put(gkey, unalignedFlags.getOrDefault(gkey, false) || ev.isUnaligned);
            timeouts.putIfAbsent(gkey, ev.alignedCheckpointTimeoutMs > 0 ? ev.alignedCheckpointTimeoutMs : DEFAULT_TIMEOUT);
            String bkey = gkey + "|" + ev.subtaskIndex;
            buckets.computeIfAbsent(bkey, k -> new ArrayList<>()).add(ev.timestampMs);
        }
        List<BufferRow> rows = new ArrayList<>();
        Map<String, List<String>> groups = new HashMap<>();
        for (String bkey : buckets.keySet()) {
            String gkey = bkey.substring(0, bkey.lastIndexOf('|'));
            groups.computeIfAbsent(gkey, k -> new ArrayList<>()).add(bkey);
        }
        for (Map.Entry<String, List<String>> entry : groups.entrySet()) {
            String gkey = entry.getKey();
            String[] parts = gkey.split("\\|");
            int cp = Integer.parseInt(parts[0]);
            int attempt = Integer.parseInt(parts[1]);
            String op = parts[2];
            List<Long> ts = new ArrayList<>();
            for (String bk : entry.getValue()) {
                ts.addAll(buckets.get(bk));
            }
            if (ts.isEmpty()) {
                continue;
            }
            long min = ts.stream().min(Long::compare).orElse(0L);
            long max = ts.stream().max(Long::compare).orElse(0L);
            int skew = (int) (max - min);
            int expected = SubtaskOperatorMapper.expectedSubtasks(op, graph);
            int received = entry.getValue().size();
            boolean unaligned = unalignedFlags.getOrDefault(gkey, false);
            int timeout = timeouts.getOrDefault(gkey, DEFAULT_TIMEOUT);
            String clazz;
            if (unaligned) {
                clazz = "UNALIGNED_DECLARED";
            } else if (received < expected) {
                clazz = "INCOMPLETE";
            } else if (skew > timeout) {
                clazz = "TIMEOUT_VIOLATION";
            } else {
                clazz = "ALIGNED_OK";
            }
            BufferRow row = new BufferRow(cp, attempt, op, skew, clazz, received, expected, min, max, "");
            String digest = BufferDigest.digest(row);
            rows.add(new BufferRow(cp, attempt, op, skew, clazz, received, expected, min, max, digest));
        }
        rows.sort(Comparator.comparingInt(BufferRow::checkpointId)
                .thenComparingInt(BufferRow::attemptId)
                .thenComparing(BufferRow::operatorId));
        Files.createDirectories(outPath.getParent());
        StringBuilder sb = new StringBuilder();
        for (BufferRow row : rows) {
            sb.append(GSON.toJson(row)).append('\n');
        }
        Files.writeString(outPath, sb.toString(), StandardCharsets.UTF_8);
    }
}
