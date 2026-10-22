import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pilot-config-validator"))
import setup_pilot
import validator


BOT_NUMBER = "+620000000099"
OWNER_ID = "620000000001@s.whatsapp.net"
GROUP_ID = "120000000000001@g.us"


class GroupSummaryManifestTests(unittest.TestCase):
    def test_one_group_manifest_observes_without_mention_and_retains_metadata_for_one_day(self):
        manifest = setup_pilot.build_one_group_manifest(BOT_NUMBER, OWNER_ID, GROUP_ID)
        pilot = manifest["x_wa_pilot_audit"]

        self.assertEqual(pilot["group_policy"], "allowlist")
        self.assertEqual(pilot["allowlisted_groups"], [GROUP_ID])
        self.assertFalse(pilot["require_mention"])
        self.assertEqual(pilot["ttl_seconds"], 86_400)
        self.assertEqual(pilot["retention_mode"], "metadata_only")
        self.assertFalse(pilot["group_auto_reply_enabled"])
        self.assertEqual(pilot["summary_delivery_policy"], "owner_dm_on_request")

        report = validator.audit_text(setup_pilot.dump_yaml(manifest))
        self.assertTrue(report["pilot_enabled"])
        self.assertEqual(report["group_count"], 1)
        self.assertFalse(report["require_mention"])
        self.assertEqual(report["retention_mode"], "metadata_only")


if __name__ == "__main__":
    unittest.main()
