# Tick clock conversion

Wall-clock seconds at tick T accumulate segment durations between tempo boundaries. Each segment contributes delta_ticks divided by ppq multiplied by microseconds_per_quarter divided by one million. Only the tempo active at each segment start applies to ticks until the next tempo event tick.
