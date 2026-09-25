package syndemit

import "github.com/terminus/gridplan/internal/runepoch"

func Allowed() bool {
    return runepoch.PlanPass() > 0
}
