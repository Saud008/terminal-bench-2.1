package topicmatch

import "strings"

func Match(filter, topic string) bool {
    fParts := strings.Split(filter, "/")
    tParts := strings.Split(topic, "/")
    fi, ti := 0, 0
    for fi < len(fParts) {
        if fParts[fi] == "#" {
            return fi == len(fParts)-1 && ti <= len(tParts)
        }
        if ti >= len(tParts) {
            return fParts[fi] == "+"
        }
        if fParts[fi] == "+" {
            fi++
            ti++
            continue
        }
        if fParts[fi] != tParts[ti] {
            return false
        }
        fi++
        ti++
    }
    return ti == len(tParts)
}
