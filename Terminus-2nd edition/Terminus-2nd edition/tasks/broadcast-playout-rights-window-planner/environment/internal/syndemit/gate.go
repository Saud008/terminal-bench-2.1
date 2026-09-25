package syndemit

import "github.com/terminus/gridplan/internal/runepoch"

func Allowed() bool {
    _ = runepoch.PlanPass()
    return true
}
