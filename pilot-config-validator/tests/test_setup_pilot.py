import io
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import setup_pilot
import validator


class SetupPilotTests(unittest.TestCase):
    def test_build_manifest_enforces_fixed_safety_policy(self):
        manifest = setup_pilot.build_manifest(
            "+620000000000",
            "620000000001@s.whatsapp.net",
        )
        pilot = manifest["x_wa_pilot_audit"]
        self.assertTrue(pilot["enabled"])
        self.assertFalse(pilot["send_enabled"])
        self.assertEqual(pilot["group_policy"], "disabled")
        self.assertEqual(pilot["allowlisted_groups"], [])
        self.assertEqual(pilot["sender_policy"], "owner_only")
        self.assertEqual(pilot["unauthorized_sender_behavior"], "reject")
        self.assertFalse(pilot["media_enabled"])
        self.assertFalse(pilot["attachments_enabled"])
        self.assertFalse(pilot["url_preview_enabled"])
        self.assertTrue(pilot["kill_switch_configured"])
        self.assertTrue(pilot["kill_switch_active"])
        self.assertEqual(pilot["ttl_seconds"], 60)
        self.assertFalse(pilot["group_tool_execution_enabled"])
        self.assertFalse(pilot["raw_message_logging_enabled"])
        self.assertTrue(pilot["default_deny"])

    def test_manifest_passes_reduced_validator_except_runtime_isolation(self):
        manifest = setup_pilot.build_manifest(
            "+620000000000",
            "620000000001@s.whatsapp.net",
        )
        report = validator.audit_text(setup_pilot.dump_yaml(manifest))
        self.assertTrue(report["pilot_enabled"])
        self.assertFalse(report["send_enabled"])
        self.assertEqual(report["group_count"], 0)
        self.assertEqual(report["runtime_isolation_status"], "BELUM_DIUJI")

    def test_one_group_manifest_has_one_allowlisted_group_and_safe_delivery_policy(self):
        manifest = setup_pilot.build_one_group_manifest(
            "+620000000000",
            "620000000001@s.whatsapp.net",
            "120000000000001@g.us",
        )
        pilot = manifest["x_wa_pilot_audit"]
        self.assertEqual(pilot["group_policy"], "allowlist")
        self.assertEqual(pilot["allowlisted_groups"], ["120000000000001@g.us"])
        # Passive observer: messages are retained as metadata for an owner-requested daily summary.
        self.assertFalse(pilot["require_mention"])
        self.assertEqual(pilot["dm_sender_policy"], "owner_only")
        self.assertFalse(pilot["send_enabled"])
        self.assertFalse(pilot["group_auto_reply_enabled"])
        self.assertTrue(pilot["temporary_group_summary_buffer_enabled"])
        self.assertEqual(pilot["summary_delivery_policy"], "owner_dm_on_request")
        self.assertFalse(pilot["gateway_start_enabled"])

    def test_two_group_manifest_has_only_two_allowlisted_groups_and_safe_delivery_policy(self):
        manifest = setup_pilot.build_two_group_manifest(
            "+620000000000",
            "620000000001@s.whatsapp.net",
            ["120000000000001@g.us", "120000000000002@g.us"],
        )
        pilot = manifest["x_wa_pilot_audit"]
        self.assertEqual(pilot["group_policy"], "allowlist")
        self.assertEqual(pilot["allowlisted_groups"], ["120000000000001@g.us", "120000000000002@g.us"])
        # Passive observer: messages are retained as metadata for an owner-requested daily summary.
        self.assertFalse(pilot["require_mention"])
        self.assertEqual(pilot["dm_sender_policy"], "owner_only")
        self.assertFalse(pilot["group_tool_execution_enabled"])
        self.assertFalse(pilot["media_enabled"])
        self.assertFalse(pilot["raw_message_logging_enabled"])
        self.assertFalse(pilot["group_auto_reply_enabled"])
        self.assertTrue(pilot["temporary_group_summary_buffer_enabled"])
        self.assertEqual(pilot["summary_delivery_policy"], "owner_dm_on_request")
        self.assertFalse(pilot["gateway_start_enabled"])

    def test_two_group_prompt_uses_one_no_echo_entry_and_writes_a_new_reduced_manifest(self):
        output = io.StringIO()
        prompts = []
        source_manifest = setup_pilot.dump_yaml(setup_pilot.build_manifest(
            "+620000000000", "620000000001@s.whatsapp.net"
        ))

        def local_input(prompt):
            prompts.append(prompt)
            return "120000000000001@g.us, 120000000000002@g.us"

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "pilot.local.yaml"
            target = Path(directory) / "pilot.two-group.local.yaml"
            source.write_text(source_manifest, encoding="utf-8")
            code = setup_pilot.main_two_groups(
                input_fn=local_input, source_path=source, output_path=target, stream=output
            )
            self.assertEqual(code, 0)
            self.assertTrue(target.is_file())
            rendered = output.getvalue()
            self.assertNotIn("120000000000001@g.us", rendered)
            self.assertNotIn("620000000001@s.whatsapp.net", rendered)
        self.assertEqual(prompts, ["Dua ID grup @g.us (pisahkan dengan koma): "])

    def test_cli_selects_one_group_local_prompt(self):
        from unittest.mock import patch
        with patch.object(setup_pilot, "main_one_group", return_value=0) as one_group:
            self.assertEqual(setup_pilot.cli(["--one-group"]), 0)
        one_group.assert_called_once_with()

    def test_cli_selects_two_group_local_prompt(self):
        from unittest.mock import patch
        with patch.object(setup_pilot, "main_two_groups", return_value=0) as two_groups:
            self.assertEqual(setup_pilot.cli(["--two-groups"]), 0)
        two_groups.assert_called_once_with()

    def test_invalid_identifiers_are_rejected(self):
        with self.assertRaises(ValueError):
            setup_pilot.build_manifest("6200", "owner")

    def test_valid_bot_and_owner_formats_are_accepted(self):
        manifest = setup_pilot.build_manifest(
            "+620000000000", "620000000001@s.whatsapp.net"
        )
        self.assertEqual(manifest["x_wa_pilot_audit"]["group_policy"], "disabled")

    def test_invalid_bot_prints_specific_message_and_creates_no_file(self):
        output = io.StringIO()
        prompts = []

        def local_input(prompt):
            prompts.append(prompt)
            return "620 000"

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "pilot.local.yaml"
            code = setup_pilot.main(input_fn=local_input, output_path=target, stream=output)
            self.assertEqual(code, 2)
            self.assertFalse(target.exists())
        self.assertEqual(len(prompts), 1)
        self.assertIn("Nomor bot tidak valid: gunakan + diikuti 8–15 digit tanpa spasi.", output.getvalue())
        self.assertNotIn("620 000", output.getvalue())

    def test_invalid_owner_prints_specific_message_and_creates_no_file(self):
        output = io.StringIO()
        values = iter(["+620000000000", "+620000000001@s.whatsapp.net"])

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "pilot.local.yaml"
            code = setup_pilot.main(input_fn=lambda _prompt: next(values), output_path=target, stream=output)
            self.assertEqual(code, 2)
            self.assertFalse(target.exists())
        self.assertIn("ID owner tidak valid: gunakan angka internasional tanpa + lalu @s.whatsapp.net.", output.getvalue())
        self.assertNotIn("+620000000001@s.whatsapp.net", output.getvalue())

    def test_status_message_never_contains_input_values(self):
        output = io.StringIO()
        setup_pilot.print_reduced_status(
            validator.audit_text(setup_pilot.dump_yaml(setup_pilot.build_manifest(
                "+620000000000", "620000000001@s.whatsapp.net"
            ))),
            stream=output,
        )
        rendered = output.getvalue()
        self.assertNotIn("620000000000", rendered)
        self.assertNotIn("620000000001@s.whatsapp.net", rendered)



if __name__ == "__main__":
    unittest.main()
