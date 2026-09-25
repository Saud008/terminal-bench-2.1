# QASM gate counting

Stage ingest records qasm_gate_count on cal-staging.json from the experiment QASM file.

Count each line after trimming leading and trailing whitespace that satisfies all of the following:

- the line ends with a semicolon
- the line starts with h (Hadamard), cx (CNOT), or measure

Do not count OPENQASM headers, include directives, qreg or creg declarations, blank lines, comments, or gate lines that use other opcodes.

The count is the total number of matching lines. This heuristic is line-based and does not parse gate arguments or qubit indices.
