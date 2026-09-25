package com.flinkskew.map;

import com.flinkskew.model.EventRecord;
import com.flinkskew.model.OperatorSpec;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.FieldNamingPolicy;
import com.google.gson.reflect.TypeToken;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public final class SubtaskOperatorMapper {
    private static final Gson GSON = new GsonBuilder()
            .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
            .create();

    private SubtaskOperatorMapper() {}

    public record Graph(List<OperatorSpec> operators) {}

    public static Graph loadGraph(Path configDir) throws IOException {
        Path graphPath = configDir.resolve("operator_graph.json");
        String raw = Files.readString(graphPath, StandardCharsets.UTF_8);
        Graph parsed = GSON.fromJson(raw, Graph.class);
        return parsed == null ? new Graph(List.of()) : parsed;
    }

    public static String mapOperator(EventRecord ev, Graph graph) {
        return ev.operatorId;
    }

    public static int expectedSubtasks(String operatorId, Graph graph) {
        for (OperatorSpec op : graph.operators()) {
            if (op.operatorId().equals(operatorId)) {
                return op.parallelism();
            }
        }
        return 1;
    }
}
