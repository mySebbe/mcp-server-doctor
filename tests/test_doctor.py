import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_server_doctor.doctor import render_result, validate_report


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

    def test_render_result_text_mentions_pass_or_fail(self):
        passing = render_result({"ok": True, "issues": [], "warnings": [], "summary": {}}, "text")
        failing = render_result({"ok": False, "issues": [{"message": "bad"}], "warnings": [], "summary": {}}, "text")

        self.assertIn("PASS", passing)
        self.assertIn("FAIL", failing)
        self.assertIn("bad", failing)

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


if __name__ == "__main__":
    unittest.main()
