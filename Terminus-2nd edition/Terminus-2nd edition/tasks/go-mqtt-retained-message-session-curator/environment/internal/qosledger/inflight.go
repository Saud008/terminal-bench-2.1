package qosledger

import "github.com/edgeiot/mqttsessctl/internal/model"

type Inflight struct {
    QoS1Pending map[string]map[int]bool
    QoS2Pending map[string]map[int]bool
}

func NewInflight() *Inflight {
    return &Inflight{
        QoS1Pending: map[string]map[int]bool{},
        QoS2Pending: map[string]map[int]bool{},
    }
}

func (in *Inflight) TrackPublish(client string, ev model.JournalEvent) bool {
    if ev.QoS == 0 {
        return true
    }
    if ev.QoS == 1 {
        if in.QoS1Pending[client] == nil {
            in.QoS1Pending[client] = map[int]bool{}
        }
        if in.QoS1Pending[client][ev.PacketID] {
            return false
        }
        in.QoS1Pending[client][ev.PacketID] = true
        return true
    }
    if in.QoS2Pending[client] == nil {
        in.QoS2Pending[client] = map[int]bool{}
    }
    in.QoS2Pending[client][ev.PacketID] = true
    return true
}

func (in *Inflight) TrackAck(client, kind string, packetID int) {
    if kind == "PUBACK" {
        delete(in.QoS1Pending[client], packetID)
    }
    if kind == "PUBCOMP" {
        delete(in.QoS2Pending[client], packetID)
    }
}
