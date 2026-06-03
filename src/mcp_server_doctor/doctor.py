"""Validation for JSON MCP capabilities reports."""

from __future__ import annotations

import json
from typing import Any


def _issue(severity: str, path: str, message: str) -> dict[str, str]:
    return {"severity": severity, "path": path, "message": message}


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_named_items(items: Any, section: str, require_schema: bool = False) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(items, list):
        return [_issue("error", section, f"{section} must be a list")]

    seen: set[str] = set()
    for index, item in enumerate(items):
        path = f"{section}[{index}]"
        if not isinstance(item, dict):
            issues.append(_issue("error", path, f"{path} must be an object"))
            continue

        name = item.get("name")
        if not _is_nonempty_string(name):
            issues.append(_issue("error", f"{path}.name", f"{path}.name must be a non-empty string"))
        elif name in seen:
            issues.append(_issue("error", f"{path}.name", f"{path}.name duplicates another {section} entry"))
        else:
            seen.add(name)

        if require_schema and not isinstance(item.get("inputSchema"), dict):
            issues.append(_issue("error", f"{path}.inputSchema", f"{path}.inputSchema must be an object"))

        if "description" in item and not isinstance(item["description"], str):
            issues.append(_issue("warning", f"{path}.description", f"{path}.description should be a string"))
    return issues


def _validate_resources(items: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(items, list):
        return [_issue("error", "resources", "resources must be a list")]

    seen: set[str] = set()
    for index, item in enumerate(items):
        path = f"resources[{index}]"
        if not isinstance(item, dict):
            issues.append(_issue("error", path, f"{path} must be an object"))
            continue
        uri = item.get("uri")
        if not _is_nonempty_string(uri):
            issues.append(_issue("error", f"{path}.uri", f"{path}.uri must be a non-empty string"))
        elif uri in seen:
            issues.append(_issue("error", f"{path}.uri", f"{path}.uri duplicates another resource"))
        else:
            seen.add(uri)
        if "name" in item and not isinstance(item["name"], str):
            issues.append(_issue("warning", f"{path}.name", f"{path}.name should be a string"))
    return issues


def validate_report(report: Any) -> dict[str, Any]:
    """Validate a parsed JSON MCP capabilities report."""
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not isinstance(report, dict):
        issue = _issue("error", "$", "report must be a JSON object")
        return {"ok": False, "issues": [issue], "warnings": [], "summary": {}}

    capabilities = report.get("capabilities", {})
    if capabilities is not None and not isinstance(capabilities, dict):
        issues.append(_issue("error", "capabilities", "capabilities must be an object when present"))
        capabilities = {}

    expected_sections = ("tools", "resources", "prompts")
    for section in expected_sections:
        if capabilities.get(section) and section not in report:
            issues.append(_issue("error", section, f"capabilities.{section} is true but {section} is missing"))

    if "tools" in report:
        for item in _validate_named_items(report["tools"], "tools", require_schema=True):
            (warnings if item["severity"] == "warning" else issues).append(item)

    if "resources" in report:
        for item in _validate_resources(report["resources"]):
            (warnings if item["severity"] == "warning" else issues).append(item)

    if "prompts" in report:
        for item in _validate_named_items(report["prompts"], "prompts"):
            (warnings if item["severity"] == "warning" else issues).append(item)

    summary = {
        "tools": len(report.get("tools", [])) if isinstance(report.get("tools", []), list) else 0,
        "resources": len(report.get("resources", [])) if isinstance(report.get("resources", []), list) else 0,
        "prompts": len(report.get("prompts", [])) if isinstance(report.get("prompts", []), list) else 0,
        "capabilities": sorted(capabilities.keys()) if isinstance(capabilities, dict) else [],
    }
    return {"ok": not issues, "issues": issues, "warnings": warnings, "summary": summary}


def render_result(result: dict[str, Any], output_format: str = "text") -> str:
    """Render validation result as JSON or human-readable text."""
    if output_format == "json":
        return json.dumps(result, indent=2, sort_keys=True) + "\n"
    if output_format != "text":
        raise ValueError(f"unsupported output format: {output_format}")

    lines = ["PASS" if result.get("ok") else "FAIL"]
    summary = result.get("summary") or {}
    if summary:
        lines.append(
            "Summary: "
            + ", ".join(f"{key}={value}" for key, value in summary.items() if key != "capabilities")
        )
    for issue in result.get("issues", []):
        lines.append(f"ERROR {issue.get('path', '$')}: {issue.get('message', '')}")
    for warning in result.get("warnings", []):
        lines.append(f"WARNING {warning.get('path', '$')}: {warning.get('message', '')}")
    return "\n".join(lines) + "\n"


def load_report(text: str) -> Any:
    """Parse report JSON from text."""
    return json.loads(text)
