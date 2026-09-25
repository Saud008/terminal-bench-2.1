package carpanel

import "fmt"

func LobbyPreview(bank string, floor int) string {
	return fmt.Sprintf("bank %s floor %d indicator", bank, floor)
}
