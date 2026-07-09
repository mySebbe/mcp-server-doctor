import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_server_doctor.doctor import apply_strict_mode, render_result, validate_report


class DoctorTests(unittest.TestCase):
    def test_validate_report_accepts_capabilities_tools_resources_and_prompts(self):
        report = {
            "capabilities": {"tools": True, "resources": True, "resourceTemplates": True, "prompts": True},
            "tools": [{"name": "search", "description": "Search docs", "inputSchema": {"type": "object"}}],
            "resources": [{"uri": "file:///tmp/a.txt", "name": "a.txt"}],
            "resourceTemplates": [{"uriTemplate": "file:///{path}", "name": "files"}],
            "prompts": [{"name": "summarize", "description": "Summarize text"}],
        }

        result = validate_report(report)

        self.assertTrue(result["ok"])
        self.assertEqual(result["summary"]["tools"], 1)
        self.assertEqual(result["summary"]["resources"], 1)
        self.assertEqual(result["summary"]["resourceTemplates"], 1)
        self.assertEqual(result["summary"]["prompts"], 1)

    def test_validate_report_reports_structural_failures(self):
        result = validate_report({"capabilities": {"tools": True}, "tools": [{"description": "missing name"}]})

        self.assertFalse(result["ok"])
        messages = "\n".join(issue["message"] for issue in result["issues"])
        self.assertIn("tools[0].name", messages)
        self.assertIn("tools[0].inputSchema", messages)

    def test_validate_report_reports_resource_template_failures(self):
        result = validate_report(
            {
                "capabilities": {"resourceTemplates": True},
                "resourceTemplates": [{"name": 42}, {"uriTemplate": "file:///{path}"}, {"uriTemplate": "file:///{path}"}],
            }
        )

        self.assertFalse(result["ok"])
        messages = "\n".join(issue["message"] for issue in result["issues"])
        warning_messages = "\n".join(warning["message"] for warning in result["warnings"])
        self.assertIn("uriTemplate", messages)
        self.assertIn("duplicates", messages)
        self.assertIn("name should be a string", warning_messages)

    def test_duplicate_tool_resource_and_prompt_identifiers_are_integrity_errors(self):
        result = validate_report(
            {
                "tools": [
                    {"name": "search", "inputSchema": {"type": "object"}},
                    {"name": "search", "inputSchema": {"type": "object"}},
                ],
                "resources": [
                    {"uri": "file:///docs/index.md"},
                    {"uri": "file:///docs/index.md"},
                ],
                "prompts": [{"name": "summarize"}, {"name": "summarize"}],
            }
        )

        self.assertFalse(result["ok"])
        duplicate_issues = [issue for issue in result["issues"] if "duplicates" in issue["message"]]
        self.assertEqual(
            {issue["path"] for issue in duplicate_issues},
            {"tools[1].name", "resources[1].uri", "prompts[1].name"},
        )
        self.assertTrue(all(issue["severity"] == "error" for issue in duplicate_issues))
        self.assertFalse(apply_strict_mode(result, strict=True)["ok"])

    def test_validate_report_treats_null_capabilities_as_absent(self):
        result = validate_report({"capabilities": None})

        self.assertTrue(result["ok"])
        self.assertEqual(result["summary"]["capabilities"], [])

    def test_render_result_text_mentions_pass_or_fail(self):
        passing = render_result({"ok": True, "issues": [], "warnings": [], "summary": {}}, "text")
        failing = render_result({"ok": False, "issues": [{"message": "bad"}], "warnings": [], "summary": {}}, "text")

        self.assertIn("PASS", passing)
        self.assertIn("FAIL", failing)
        self.assertIn("bad", failing)

    def test_apply_strict_mode_treats_warnings_as_failures(self):
        result = validate_report({"resources": [{"uri": "file:///tmp/a.txt", "name": 42}]})

        strict = apply_strict_mode(result, strict=True)

        self.assertTrue(result["ok"])
        self.assertFalse(strict["ok"])
        self.assertTrue(strict["summary"]["strict"])

    def test_cli_reads_stdin_and_emits_json(self):
        payload = json.dumps({"capabilities": {"tools": True}, "tools": []})
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

        completed = subprocess.run(
            [sys.executable, "-m", "mcp_server_doctor", "--format", "json"],
            input=payload,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["ok"])

    def test_cli_strict_mode_returns_nonzero_for_warnings(self):
        payload = json.dumps({"resources": [{"uri": "file:///tmp/a.txt", "name": 42}]})
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

        completed = subprocess.run(
            [sys.executable, "-m", "mcp_server_doctor", "--format", "json", "--strict"],
            input=payload,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        self.assertTrue(json.loads(completed.stdout)["summary"]["strict"])

    def test_cli_rejects_oversized_stdin(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

        completed = subprocess.run(
            [sys.executable, "-m", "mcp_server_doctor", "--max-input-bytes", "1"],
            input="{}",
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("--max-input-bytes", completed.stderr)

    def test_cli_rejects_oversized_file_before_reading_contents(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "report.json")
            with open(path, "wb") as handle:
                handle.write(b"{}")
            completed = subprocess.run(
                [sys.executable, "-m", "mcp_server_doctor", "--max-input-bytes", "1", path],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("--max-input-bytes", completed.stderr)

    def test_cli_accepts_input_at_byte_limit(self):
        payload = '{"capabilities": {}}'
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "mcp_server_doctor",
                "--format",
                "json",
                "--max-input-bytes",
                str(len(payload.encode("utf-8"))),
            ],
            input=payload,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["ok"])

    def test_cli_rejects_non_positive_input_limit(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))

        completed = subprocess.run(
            [sys.executable, "-m", "mcp_server_doctor", "--max-input-bytes", "0"],
            input="{}",
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("positive integer", completed.stderr)


if __name__ == "__main__":
    unittest.main()
