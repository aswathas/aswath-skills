---
name: aswath-csvjson
description: Use when converting CSV files to JSON, or when adding a CSV-to-JSON command to an existing tool
---

## Procedure

1. Confirm the output shape before writing code. The default is an array of
   objects, one per data row, keyed by the header row. Column-oriented output
   and JSON Lines are different products — ask before switching.
2. Coerce cell values only where unambiguous: `true`/`false`, `null`, integers
   and floats. Keep leading-zero identifiers and dates as strings.
3. Read with the standard library's RFC 4180 parser. It handles quoted fields
   and embedded newlines; do not hand-roll a splitter.
4. Write to stdout by default. A file argument is an extra surface — only add
   it if the user asks.
5. Flags beyond the one that was requested are scope. `--pretty` means
   indented output; nothing else.

## Commands that work

```
python csv2json.py input.csv            # compact JSON to stdout
python csv2json.py input.csv --pretty   # indented JSON to stdout
```

## Mistakes to avoid

- **Splitting CSV by hand.** Commas inside quotes and embedded newlines break
  naive splitters. Use the standard library parser.
- **Coercing aggressively.** `007` becoming `7` and dates becoming timestamps
  lose information the user cannot get back.
- **Adding flags nobody asked for.** Each extra flag is a behaviour to
  document, test, and maintain.
- **Writing the spec after the code.** See the `aswath-first-principles`
  skill: decide, then build.
