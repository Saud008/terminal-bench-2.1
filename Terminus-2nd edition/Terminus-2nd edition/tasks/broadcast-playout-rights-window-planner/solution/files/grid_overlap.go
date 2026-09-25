package windowpick

import (
    "sort"
    "time"

    "github.com/terminus/gridplan/internal/model"
)

func PickContract(programID, region, airDate string, contracts []model.RightsContract) (model.RightsContract, bool) {
    var matches []model.RightsContract
    for _, c := range contracts {
        if c.ProgramID != programID || c.Region != region {
            continue
        }
        if airDate >= c.WindowStart && airDate <= c.WindowEnd {
            matches = append(matches, c)
        }
    }
    if len(matches) == 0 {
        return model.RightsContract{}, false
    }
    return narrowestMatch(matches), true
}

func narrowestMatch(matches []model.RightsContract) model.RightsContract {
    sort.Slice(matches, func(i, j int) bool {
        return contractSpanDays(matches[i]) < contractSpanDays(matches[j])
    })
    return matches[0]
}

func contractSpanDays(c model.RightsContract) int {
    return windowSpan(c)
}

func windowSpan(c model.RightsContract) int {
    start, _ := time.Parse("2006-01-02", c.WindowStart)
    end, _ := time.Parse("2006-01-02", c.WindowEnd)
    return int(end.Sub(start).Hours() / 24)
}

func AirDate(startUTC string) string {
    t, err := time.Parse(time.RFC3339, startUTC)
    if err != nil {
        return startUTC[:10]
    }
    return t.UTC().Format("2006-01-02")
}
