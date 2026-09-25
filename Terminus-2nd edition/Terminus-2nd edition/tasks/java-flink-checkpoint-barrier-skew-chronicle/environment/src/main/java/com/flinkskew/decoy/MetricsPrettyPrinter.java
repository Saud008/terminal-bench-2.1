package com.flinkskew.decoy;

import java.util.Map;

/** Pretty printer for Flink metrics snapshots — not used by chronicle pipeline. */
public final class MetricsPrettyPrinter {
    private MetricsPrettyPrinter() {}

    public static String render(Map<String, Double> metrics) {
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, Double> e : metrics.entrySet()) {
            sb.append(e.getKey()).append('=').append(String.format("%.3f", e.getValue())).append('\n');
        }
        return sb.toString();
    }
}
