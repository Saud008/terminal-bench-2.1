# Variable merge on incident resolution

Working variables start as scenario variables.inputs.

When any incident exists, apply variables.incident_overlay to the working map after incidents are processed. Overlay keys must not replace source keys referenced as values in variables.output_mapping. Protected source keys keep their pre-overlay values.

After merge, build resolved_outputs by mapping each output_mapping entry: output key maps to working[source key].

Export variable_snapshot contains working and resolved_outputs separately. Do not store output_mapping inside resolved_outputs.
