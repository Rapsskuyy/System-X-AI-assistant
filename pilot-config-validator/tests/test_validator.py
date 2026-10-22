import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import validator

DUMMY = """x_wa_pilot_audit:
  enabled: true
  bot_number: "+620000000000"
  send_enabled: false
  group_policy: disabled
  allowlisted_groups: []
  owner_id: synthetic-owner-001@s.whatsapp.net
  sender_policy: owner_only
  unauthorized_sender_behavior: reject
  media_enabled: false
  attachments_enabled: false
  url_preview_enabled: false
  kill_switch_configured: true
  kill_switch_active: true
  ttl_seconds: 60
  group_tool_execution_enabled: false
  raw_message_logging_enabled: false
  default_deny: true
  unrelated_secret: DUMMY_SECRET_MARKER
"""


class ValidatorTests(unittest.TestCase):
    def test_synthetic_audit_has_only_reduced_fields(self):
        report = validator.audit_text(DUMMY)
        self.assertEqual(set(report), set(validator.FIELDS))
        self.assertTrue(report["config_readable"])
        self.assertIs(report["pilot_enabled"], True)
        self.assertIs(report["send_enabled"], False)
        self.assertEqual(report["group_count"], 0)
        self.assertIs(report["owner_configured"], True)
        self.assertIs(report["media_enabled"], False)
        self.assertIs(report["url_preview_enabled"], False)
        self.assertIs(report["kill_switch_configured"], True)
        self.assertEqual(report["runtime_isolation_status"], "BELUM_DIUJI")
        output = validator.render(report)
        for forbidden in ("synthetic-owner-001", "DUMMY_SECRET_MARKER"):
            self.assertNotIn(forbidden, output)

    def test_realistic_hermes_yaml_without_explicit_pilot_block_is_unknown(self):
        report = validator.audit_text("gateway:\n  trust_env: true\nplatform_toolsets:\n  whatsapp: [hermes-whatsapp]\n")
        self.assertTrue(report["config_readable"])
        self.assertIsNone(report["pilot_enabled"])
        self.assertIsNone(report["send_enabled"])
        self.assertIsNone(report["group_count"])
        self.assertIsNone(report["owner_configured"])
        self.assertFalse(validator.ready(report))

    def test_malformed_yaml_fails_closed_without_echoing_payload(self):
        report = validator.audit_text("x_wa_pilot_audit: [DUMMY_SECRET_MARKER\n")
        self.assertFalse(report["config_readable"])
        self.assertIsNone(report["send_enabled"])
        self.assertNotIn("DUMMY_SECRET_MARKER", validator.render(report))

    def test_missing_file_fails_closed(self):
        report = validator.audit_file(ROOT / "data" / "not-a-file.yaml")
        self.assertFalse(report["config_readable"])
        self.assertIsNone(report["pilot_enabled"])

    def test_attachment_enabled_counts_as_media_enabled(self):
        report = validator.audit_text(DUMMY.replace("attachments_enabled: false", "attachments_enabled: true"))
        self.assertIs(report["media_enabled"], True)

    def test_incomplete_policy_is_unknown_not_safe(self):
        report = validator.audit_text(DUMMY.replace("  send_enabled: false\n", "").replace("  attachments_enabled: false\n", ""))
        self.assertIsNone(report["send_enabled"])
        self.assertIsNone(report["media_enabled"])

    def test_pilot_status_requires_all_non_output_safety_controls(self):
        unsafe = DUMMY.replace("  ttl_seconds: 60", "  ttl_seconds: 120")
        self.assertIsNone(validator.audit_text(unsafe)["pilot_enabled"])
        unsafe = DUMMY.replace("  group_tool_execution_enabled: false", "  group_tool_execution_enabled: true")
        self.assertIsNone(validator.audit_text(unsafe)["pilot_enabled"])
        unsafe = DUMMY.replace("  raw_message_logging_enabled: false", "  raw_message_logging_enabled: true")
        self.assertIsNone(validator.audit_text(unsafe)["pilot_enabled"])
        unsafe = DUMMY.replace("  default_deny: true", "  default_deny: false")
        self.assertIsNone(validator.audit_text(unsafe)["pilot_enabled"])

    def test_one_group_policy_is_reported_without_identifiers(self):
        one_group = DUMMY.replace("  group_policy: disabled", "  group_policy: allowlist").replace(
            "  allowlisted_groups: []", "  allowlisted_groups: [120000000000001@g.us]"
        ).replace("  sender_policy: owner_only", "  dm_sender_policy: owner_only").replace(
            "  ttl_seconds: 60", "  ttl_seconds: 86400"
        ) + """  require_mention: false
  retention_mode: metadata_only
  group_auto_reply_enabled: false
  temporary_group_summary_buffer_enabled: true
  summary_delivery_policy: owner_dm_on_request
  gateway_start_enabled: false
"""
        report = validator.audit_text(one_group)
        self.assertIs(report["pilot_enabled"], True)
        self.assertEqual(report["group_count"], 1)
        self.assertNotIn("120000000000001@g.us", validator.render(report))

    def test_two_group_policy_is_reported_without_identifiers(self):
        two_group = DUMMY.replace("  group_policy: disabled", "  group_policy: allowlist").replace(
            "  allowlisted_groups: []", "  allowlisted_groups: [120000000000001@g.us, 120000000000002@g.us]"
        ).replace("  sender_policy: owner_only", "  dm_sender_policy: owner_only").replace(
            "  ttl_seconds: 60", "  ttl_seconds: 86400"
        ) + """  require_mention: false
  retention_mode: metadata_only
  group_auto_reply_enabled: false
  temporary_group_summary_buffer_enabled: true
  summary_delivery_policy: owner_dm_on_request
  gateway_start_enabled: false
"""
        report = validator.audit_text(two_group)
        self.assertIs(report["pilot_enabled"], True)
        self.assertEqual(report["group_count"], 2)
        self.assertIs(report["require_mention"], False)
        self.assertIs(report["dm_owner_only"], True)
        self.assertIs(report["group_tool_execution_enabled"], False)
        self.assertIs(report["group_auto_reply_enabled"], False)
        self.assertIs(report["temporary_group_summary_buffer_enabled"], True)
        self.assertEqual(report["summary_delivery_policy"], "owner_dm_on_request")
        self.assertIs(report["gateway_start_enabled"], False)
        self.assertNotIn("120000000000001@g.us", validator.render(report))

    def test_dm_owner_only_policy_requires_groups_disabled_and_empty(self):
        one_group = DUMMY.replace("  allowlisted_groups: []", "  allowlisted_groups: [synthetic-group-001@g.us]")
        report = validator.audit_text(one_group)
        self.assertEqual(report["group_count"], 1)
        self.assertIsNone(report["pilot_enabled"])
        enabled_groups = DUMMY.replace("  group_policy: disabled", "  group_policy: allowlist")
        self.assertIsNone(validator.audit_text(enabled_groups)["pilot_enabled"])

    def test_only_owner_and_rejection_of_other_senders_are_required(self):
        broader = DUMMY.replace("  sender_policy: owner_only", "  sender_policy: allowlist")
        self.assertIsNone(validator.audit_text(broader)["pilot_enabled"])
        permissive = DUMMY.replace("  unauthorized_sender_behavior: reject", "  unauthorized_sender_behavior: ignore")
        self.assertIsNone(validator.audit_text(permissive)["pilot_enabled"])

    def test_kill_switch_must_be_configured_and_active(self):
        report = validator.audit_text(DUMMY.replace("  kill_switch_active: true", "  kill_switch_active: false"))
        self.assertIs(report["kill_switch_configured"], False)

    def test_bot_number_is_required_but_never_rendered(self):
        report = validator.audit_text(DUMMY.replace("  bot_number: \"+620000000000\"\n", ""))
        self.assertIsNone(report["pilot_enabled"])
        self.assertNotIn("+620000000000", validator.render(validator.audit_text(DUMMY)))

    def test_dummy_cli_exposes_reduced_json_and_refuses_runtime_claim(self):
        completed = subprocess.run([sys.executable, "-B", str(ROOT / "validator.py"), "--config", str(ROOT / "data" / "dummy_config.yaml")], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, "")
        report = json.loads(completed.stdout)
        self.assertEqual(set(report), set(validator.FIELDS))
        self.assertEqual(report["group_count"], 0)
        self.assertNotIn("synthetic-owner", completed.stdout)


if __name__ == "__main__":
    unittest.main()
