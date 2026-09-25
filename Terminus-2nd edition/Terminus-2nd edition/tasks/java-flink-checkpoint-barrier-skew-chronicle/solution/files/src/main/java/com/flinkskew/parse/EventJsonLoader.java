package com.flinkskew.parse;

import com.flinkskew.model.EventRecord;
import com.flinkskew.util.JsonUtil;
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
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class EventJsonLoader {
    private static final Gson GSON = new GsonBuilder()
            .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
            .create();

    private EventJsonLoader() {}

    public static void load(Path inputDir, Path outFile) throws IOException {
        List<EventRecord> rows = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        try (var paths = Files.list(inputDir)) {
            List<Path> files = paths.filter(p -> p.getFileName().toString().endsWith(".jsonl"))
                    .sorted()
                    .toList();
            for (Path file : files) {
                for (String line : Files.readAllLines(file, StandardCharsets.UTF_8)) {
                    if (line.isBlank()) {
                        continue;
                    }
                    EventRecord ev = GSON.fromJson(line, EventRecord.class);
                    String key = ev.checkpointId + "|" + ev.attemptId + "|" + ev.operatorId + "|" + ev.subtaskIndex
                            + "|" + ev.eventKind + "|" + ev.timestampMs;
                    if (!seen.add(key)) {
                        continue;
                    }
                    rows.add(ev);
                }
            }
        }
        rows.sort(Comparator
                .comparingLong((EventRecord e) -> e.timestampMs)
                .thenComparing(e -> e.operatorId)
                .thenComparingInt(e -> e.subtaskIndex));
        Files.createDirectories(outFile.getParent());
        JsonUtil.writePretty(outFile, rows);
    }
}
