# mcp-server-doctor

`mcp-server-doctor` validates JSON MCP capability reports from a file or stdin and emits pass/fail output as text or JSON.

## 0.1.1 Highlights

- Capability reports now validate MCP `resourceTemplates`.
- Summaries include resource template counts and duplicate `uriTemplate` detection.

## Install

```bash
python -m pip install .
```

## CLI

```bash
mcp-server-doctor report.json
cat report.json | mcp-server-doctor --format json
python -m mcp_server_doctor --format text < report.json
```

Exit codes:

- `0`: validation passed
- `1`: validation failed
- `2`: invalid input, unreadable file, or invalid JSON

## Report Shape

The validator expects a JSON object that may include:

- `capabilities`: object with `tools`, `resources`, and `prompts` booleans
- `tools`: list of objects with `name` and `inputSchema`
- `resources`: list of objects with `uri`
- `prompts`: list of objects with `name`

## Development

```bash
python -m unittest discover -s tests
```
