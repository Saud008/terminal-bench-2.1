package com.flinkskew.watermark;

import com.flinkskew.model.EventRecord;

public final class WatermarkGuard {
    private WatermarkGuard() {}

    public static boolean countsAsBarrierReceipt(EventRecord ev) {
        if ("CHECKPOINT_BARRIER".equals(ev.eventKind)) {
            return true;
        }
        if ("WATERMARK".equals(ev.eventKind)) {
            return false;
        }
        return false;
    }
}
