The mdtable CLI under /app/crates/mdtable exports pipe-style Markdown tables from files under /app/fixtures/tables/ to JSON or HTML. The Rust libraries under /app/crates/mdtable-core disagree with the contracts in /app/docs/.

Repair the parser and exporters so export succeeds for every table listed in /app/docs/fixture-catalog.md. Use mdtable export with --input pointing at a fixture path, --export for the output path, and --format json or html; use mdtable publish with --export and --format per the CLI surface in /app/README.md.

Successful export must parse tables, place cells on a logical grid, write /app/state/grid.snapshot.json per /app/docs/grid-snapshot.md, and publish JSON per /app/docs/table-export-schema.md and HTML per /app/docs/html-export-contract.md. Table detection, alignment rows, escaped pipes, colspan and rowspan markers, and grid placement must follow /app/docs/table-extension-contract.md.

Rebuild from /app and install /usr/local/bin/mdtable so those exports succeed. Do not hardcode export files. Do not edit /app/docs/ or /app/fixtures/.
