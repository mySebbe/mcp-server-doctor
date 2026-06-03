# Contributing

Thanks for improving `mcp-server-doctor`.

## Local Setup

```bash
python -m pip install -e .
python -m unittest discover -s tests
```

## Guidelines

- Keep the package stdlib-first.
- Add or update `unittest` coverage for behavior changes.
- Avoid network calls in tests.
- Keep CLI output stable and documented.

Release instructions live in [PUBLISHING.md](PUBLISHING.md).
