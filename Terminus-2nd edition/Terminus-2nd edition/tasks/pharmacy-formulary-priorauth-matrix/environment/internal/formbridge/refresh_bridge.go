package formbridge

import "github.com/terminus/formulatrix/internal/refreshpass"

func RunRefreshPass(scenario string) error {
    return refreshpass.Run(scenario)
}
