package detach

func IsDetached(allDetachedFlags []bool) bool {
    for _, f := range allDetachedFlags {
        if f {
            return true
        }
    }
    return false
}
