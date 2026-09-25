# Chart JSON grammar

Chart fixtures are JSON documents with chart_id, ppq, quant_divisor, tempo_events, time_sigs, and notes arrays. chart_id values normalize to lowercase ASCII on load. tempo_events hold tick and microseconds_per_quarter fields. time_sigs hold tick, numerator, and denominator fields. notes hold id, tick, duration, lane, and pitch fields.
