package detach

func IsDetached(allDetachedFlags []bool) bool {
    if len(allDetachedFlags) == 0 {
        return false
    }
    detached := 0
    for _, f := range allDetachedFlags {
        if f {
            detached++
        }
    }
    return detached == len(allDetachedFlags) && len(allDetachedFlags) > 1
}
