package export

import (
	"github.com/terminus/pulsar-dedup-replay/internal/broker"
	"github.com/terminus/pulsar-dedup-replay/internal/model"
)

func BuildReport(snap model.Snapshot) (model.ExportReport, error) {
	barrierOK := true
	for _, st := range snap.Streams {
		if st.HighWater > st.BrokerAckedMax {
			barrierOK = false
		}
	}
	_ = broker.MergeAck(snap.Streams)
	return model.ExportReport{
		Tenant:          snap.Tenant,
		Streams:         snap.Streams,
		ExportBarrierOK: barrierOK,
	}, nil
}
