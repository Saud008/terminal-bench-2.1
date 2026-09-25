package com.flinkskew.util;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.FieldNamingPolicy;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

public final class JsonUtil {
    private static final Gson PRETTY = new GsonBuilder()
            .setPrettyPrinting()
            .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
            .create();
    private static final Gson PLAIN = new GsonBuilder()
            .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
            .create();

    private JsonUtil() {}

    public static void writePretty(Path path, Object value) throws IOException {
        Files.createDirectories(path.getParent());
        Files.writeString(path, PRETTY.toJson(value), StandardCharsets.UTF_8);
    }

    public static Map<String, Object> readMap(Path path) throws IOException {
        String raw = Files.readString(path, StandardCharsets.UTF_8);
        return PLAIN.fromJson(raw, new TypeToken<Map<String, Object>>() {}.getType());
    }
}
