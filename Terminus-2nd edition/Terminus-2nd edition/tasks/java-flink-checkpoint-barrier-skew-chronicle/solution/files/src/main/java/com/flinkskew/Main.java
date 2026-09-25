package com.flinkskew;

import com.flinkskew.align.BarrierAligner;
import com.flinkskew.emit.ChronicleWriter;
import com.flinkskew.parse.EventJsonLoader;

import java.nio.file.Path;

public final class Main {
    private Main() {}

    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            usage();
            System.exit(2);
        }
        switch (args[0]) {
            case "load-events" -> runLoadEvents(args);
            case "align-barriers" -> runAlignBarriers(args);
            case "emit-chronicle" -> runEmitChronicle(args);
            default -> {
                usage();
                System.exit(2);
            }
        }
    }

    private static void usage() {
        System.err.println("java -jar flink-skew.jar load-events --input DIR --out PATH");
        System.err.println("java -jar flink-skew.jar align-barriers --index PATH --out PATH");
        System.err.println("java -jar flink-skew.jar emit-chronicle --buffer PATH --out PATH");
    }

    private static void runLoadEvents(String[] args) throws Exception {
        Path input = null;
        Path out = null;
        for (int i = 1; i < args.length; i++) {
            if ("--input".equals(args[i]) && i + 1 < args.length) {
                input = Path.of(args[++i]);
            } else if ("--out".equals(args[i]) && i + 1 < args.length) {
                out = Path.of(args[++i]);
            } else {
                throw new IllegalArgumentException("unknown flag " + args[i]);
            }
        }
        if (input == null || out == null) {
            throw new IllegalArgumentException("load-events requires --input and --out");
        }
        EventJsonLoader.load(input, out);
    }

    private static void runAlignBarriers(String[] args) throws Exception {
        Path index = null;
        Path out = null;
        for (int i = 1; i < args.length; i++) {
            if ("--index".equals(args[i]) && i + 1 < args.length) {
                index = Path.of(args[++i]);
            } else if ("--out".equals(args[i]) && i + 1 < args.length) {
                out = Path.of(args[++i]);
            } else {
                throw new IllegalArgumentException("unknown flag " + args[i]);
            }
        }
        if (index == null || out == null) {
            throw new IllegalArgumentException("align-barriers requires --index and --out");
        }
        BarrierAligner.align(index, out);
    }

    private static void runEmitChronicle(String[] args) throws Exception {
        Path buffer = null;
        Path out = null;
        for (int i = 1; i < args.length; i++) {
            if ("--buffer".equals(args[i]) && i + 1 < args.length) {
                buffer = Path.of(args[++i]);
            } else if ("--out".equals(args[i]) && i + 1 < args.length) {
                out = Path.of(args[++i]);
            } else {
                throw new IllegalArgumentException("unknown flag " + args[i]);
            }
        }
        if (buffer == null || out == null) {
            throw new IllegalArgumentException("emit-chronicle requires --buffer and --out");
        }
        ChronicleWriter.emit(buffer, out);
    }
}
