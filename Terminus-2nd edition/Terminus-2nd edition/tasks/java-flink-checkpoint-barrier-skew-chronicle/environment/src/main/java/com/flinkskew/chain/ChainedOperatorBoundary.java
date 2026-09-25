package com.flinkskew.chain;

import com.flinkskew.model.EventRecord;
import com.flinkskew.model.OperatorSpec;
import com.flinkskew.map.SubtaskOperatorMapper;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class ChainedOperatorBoundary {
    private ChainedOperatorBoundary() {}

    public static boolean acceptReceipt(EventRecord ev, String mappedOperator, SubtaskOperatorMapper.Graph graph) {
        OperatorSpec spec = findSpec(mappedOperator, graph.operators());
        if (spec == null) {
            return true;
        }
        if (spec.chainHead() && !spec.chainTail()) {
            OperatorSpec next = nextInChain(spec, graph.operators());
            if (next != null && ev.operatorId.equals(next.operatorId())) {
                return false;
            }
        }
        return true;
    }

    private static OperatorSpec findSpec(String operatorId, List<OperatorSpec> ops) {
        for (OperatorSpec op : ops) {
            if (op.operatorId().equals(operatorId)) {
                return op;
            }
        }
        return null;
    }

    private static OperatorSpec nextInChain(OperatorSpec head, List<OperatorSpec> ops) {
        int idx = head.vertexIndex();
        for (OperatorSpec op : ops) {
            if (op.vertexIndex() == idx + 1) {
                return op;
            }
        }
        return null;
    }
}
