package com.flinkskew.model;

import com.google.gson.annotations.SerializedName;

public final class OperatorSpec {
    @SerializedName("operator_id")
    public String operatorId;
    @SerializedName("parallelism")
    public int parallelism;
    @SerializedName("vertex_index")
    public int vertexIndex;
    @SerializedName("chain_head")
    public boolean chainHead;
    @SerializedName("chain_tail")
    public boolean chainTail;

    public String operatorId() { return operatorId; }
    public int parallelism() { return parallelism; }
    public int vertexIndex() { return vertexIndex; }
    public boolean chainHead() { return chainHead; }
    public boolean chainTail() { return chainTail; }
}
