# Security Review: July 2026

## Executive Summary

The review covered the local JSON input path, capability-list integrity checks, malformed-input handling, dependency metadata, and the package build. The main resource-exhaustion risk was the former unbounded `read()` of file and stdin input; it is remediated by a 10 MiB default limit, an explicit `--max-input-bytes` override, a file-size pre-check, and bounded chunked reads. Duplicate tool names, resource URIs, and prompt names are enforced as blocking integrity errors.

No unresolved high-severity finding was identified by the scoped tests, Bandit scan, dependency audit, or build verification below.

## Scope and Method

- Repository: `mcp-server-doctor`
- Branch: `codex/security-reliability-july-2026`
- Review date: 2026-07-09
- Input boundary: `src/mcp_server_doctor/__main__.py:13-67`
- Report validation: `src/mcp_server_doctor/doctor.py:29-64,100-126`
- Test coverage: `tests/test_doctor.py:54-82,135-211`
- Runtime dependencies: none declared in `pyproject.toml`
- Verification runtime: Python 3.14.6 on Windows

The following checks were run after the implementation:

```text
python -m unittest discover -s tests
python -m ruff check .
python -m bandit -r src
python -m pip_audit
python -m build --sdist --wheel
```

All five commands completed successfully on 2026-07-09.

## Findings and Controls

### SEC-001: Unbounded report input

- Severity: Medium
- Status: Fixed
- Risk: A file or pipe containing unexpectedly large JSON could cause excessive memory use before validation began.
- Evidence: The input boundary now checks regular-file size with `os.fstat()` at `src/mcp_server_doctor/__main__.py:63-66` and reads both sources in bounded chunks at `src/mcp_server_doctor/__main__.py:34-52`.
- Mitigation: The default is 10 MiB. Operators can set a positive explicit limit with `--max-input-bytes`; an over-limit input returns exit code `2` without attempting JSON parsing.
- Regression coverage: `tests/test_doctor.py:135-195` covers oversized stdin, oversized files, and input exactly at the limit.

### SEC-002: Duplicate capability identifiers

- Severity: Medium
- Status: Enforced
- Risk: Duplicate names or URIs can make a capability report ambiguous and cause consumers to address the wrong tool, resource, or prompt.
- Control: Duplicate tool names, resource URIs, and prompt names produce `error` issues at `src/mcp_server_doctor/doctor.py:29-35,56-62`. They fail in normal mode and remain failures in strict mode; unrelated type warnings retain the existing strict-mode behavior.
- Regression coverage: `tests/test_doctor.py:54-76` and the existing resource-template duplicate test.

### SEC-003: Null capability metadata crash

- Severity: Low
- Status: Fixed
- Risk: A report with `"capabilities": null` could trigger an exception instead of returning a validation result.
- Mitigation: Null capability metadata is treated as absent at `src/mcp_server_doctor/doctor.py:100-105`, while non-object values remain validation errors.
- Regression coverage: `tests/test_doctor.py:78-82`.

## Automated Check Results

- Unit tests: PASS, `Ran 13 tests`, `OK`.
- Ruff: PASS, `All checks passed!`.
- Bandit 1.9.4: PASS, 235 lines scanned, 0 issues at all severities and confidence levels.
- pip-audit 2.10.1: PASS, `No known vulnerabilities found`; the active environment skipped `smolagents 1.27.0.dev0` because it is not available on PyPI. The project itself declares no runtime dependencies.
- Build 1.5.0: PASS, created `mcp_server_doctor-0.1.2.tar.gz` and `mcp_server_doctor-0.1.2-py3-none-any.whl`.

## Residual Risk and Follow-Up

The size limit bounds input bytes but does not impose separate limits on JSON nesting depth or individual capability fields. Those limits can be added if reports will be accepted from less-trusted remote automation. The CLI remains intentionally local and makes no network calls.
