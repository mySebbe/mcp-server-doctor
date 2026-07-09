# mcp-server-doctor

`mcp-server-doctor` validates JSON MCP capability reports from a file or stdin and emits pass/fail output as text or JSON.

## 0.1.2 Highlights

- CI users can now pass `--strict` to treat warnings as validation failures.
- JSON summaries include the active strict-mode setting for auditability.

## Unreleased Security Hardening

- File and stdin input is limited to 10 MiB by default and is read in bounded chunks.
- Use `--max-input-bytes BYTES` to select a different positive limit. Oversized input exits with code `2` before JSON parsing.
- Duplicate tool names, resource URIs, and prompt names are integrity errors and therefore always fail validation. Other warnings remain non-blocking unless `--strict` is enabled.

## Install

```bash
python -m pip install .
```

## CLI

```bash
mcp-server-doctor report.json
cat report.json | mcp-server-doctor --format json
cat report.json | mcp-server-doctor --format json --strict
mcp-server-doctor --max-input-bytes 5242880 report.json
python -m mcp_server_doctor --format text < report.json
```

Exit codes:

- `0`: validation passed
- `1`: validation failed, or warnings were present with `--strict`
- `2`: invalid input, unreadable file, or invalid JSON

## Report Shape

The validator expects a JSON object that may include:

- `capabilities`: object with `tools`, `resources`, and `prompts` booleans
- `tools`: list of objects with `name` and `inputSchema`
- `resources`: list of objects with `uri`
- `prompts`: list of objects with `name`

Tool names, resource URIs, and prompt names must be unique within their respective lists.

## Development

```bash
python -m unittest discover -s tests
```
