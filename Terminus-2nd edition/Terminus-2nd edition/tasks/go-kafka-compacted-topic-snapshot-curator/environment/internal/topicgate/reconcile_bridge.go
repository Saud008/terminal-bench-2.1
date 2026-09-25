package topicgate

import "github.com/terminus/kcompactctl/internal/sealpass"

func RunReconcilePass(topic, scenario string) error {
    return sealpass.Run(topic, scenario)
}
