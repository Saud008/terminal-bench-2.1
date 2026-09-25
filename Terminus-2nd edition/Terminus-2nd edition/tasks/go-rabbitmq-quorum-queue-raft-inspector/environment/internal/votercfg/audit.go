package votercfg

import (
    "encoding/json"
    "os"

    "github.com/terminus/qqraftctl/internal/model"
    "github.com/terminus/qqraftctl/internal/workpad"
)

func WriteAudit(cluster, scenario string) error {
    st, err := workpad.Read(workpad.DefaultPath)
    if err != nil {
        return err
    }
    rep := model.MembershipReport{
        Cluster: cluster, Scenario: scenario,
        MemberCount: len(st.Membership), VoterIDs: st.Membership,
        FindingCount: len(st.Membership),
    }
    raw, err := json.MarshalIndent(rep, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile("/app/work/replica-membership-report.json", append(raw, '\n'), 0o644)
}
