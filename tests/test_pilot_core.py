import unittest
from datetime import datetime, timezone

import pilot_core


GROUP_ID = "120000000000001@g.us"
OWNER_ID = "620000000001@s.whatsapp.net"


class PilotCoreTests(unittest.TestCase):
    def setUp(self):
        self.policy = pilot_core.PilotPolicy(
            group_id=GROUP_ID,
            owner_id=OWNER_ID,
            bot_id="620000000099@s.whatsapp.net",
            ttl_seconds=60,
        )
        self.controller = pilot_core.PilotController(self.policy)

    def test_allowlisted_mention_is_summarized_for_owner_on_request(self):
        result = self.controller.observe_group_message(
            {
                "chat_id": GROUP_ID,
                "sender": "620000000002@s.whatsapp.net",
                "text": "@X Deadline proposal Jumat. Rapat review besok jam 09:00.",
                "mentions_bot": True,
                "received_at": 100,
            }
        )
        self.assertEqual(result["status"], "buffered")

        response = self.controller.handle_owner_dm(
            {"sender": OWNER_ID, "text": "ringkas grup", "received_at": 110}
        )
        self.assertEqual(response["status"], "summary_ready")
        self.assertEqual(response["outbound"]["recipient"], OWNER_ID)
        self.assertEqual(response["outbound"]["kind"], "summary")
        self.assertIn("Deadline", response["outbound"]["body"])
        self.assertIn("Rapat", response["outbound"]["body"])

    def test_owner_reminder_creates_owner_only_outbound_intent(self):
        response = self.controller.handle_owner_dm(
            {
                "sender": OWNER_ID,
                "text": "ingatkan saya rapat jam 09:00, 5 menit sebelumnya",
                "received_at": 100,
            }
        )
        self.assertEqual(response["status"], "reminder_ready")
        self.assertEqual(response["outbound"]["recipient"], OWNER_ID)
        self.assertEqual(response["outbound"]["kind"], "reminder")
        self.assertEqual(response["outbound"]["scheduled_for"], "08:55")

    def test_non_owner_and_non_allowlisted_messages_never_create_outbound_intents(self):
        group_result = self.controller.observe_group_message(
            {
                "chat_id": "120000000000099@g.us",
                "sender": "620000000002@s.whatsapp.net",
                "text": "@X Deadline hari ini",
                "mentions_bot": True,
                "received_at": 100,
            }
        )
        dm_result = self.controller.handle_owner_dm(
            {"sender": "620000000003@s.whatsapp.net", "text": "ringkas", "received_at": 110}
        )
        self.assertEqual(group_result["status"], "ignored_not_allowlisted")
        self.assertEqual(dm_result["status"], "ignored_not_owner")
        self.assertIsNone(dm_result["outbound"])

    def test_ttl_removes_observed_content_before_summary(self):
        self.controller.observe_group_message(
            {
                "chat_id": GROUP_ID,
                "sender": "620000000002@s.whatsapp.net",
                "text": "@X Deadline proposal hari ini",
                "mentions_bot": True,
                "received_at": 100,
            }
        )
        response = self.controller.handle_owner_dm(
            {"sender": OWNER_ID, "text": "ringkas", "received_at": 160}
        )
        self.assertEqual(response["status"], "summary_empty")
        self.assertIsNone(response["outbound"])

    def test_unmentioned_allowlisted_message_is_retained_as_metadata_for_daily_owner_summary(self):
        controller = pilot_core.PilotController(
            pilot_core.PilotPolicy(
                group_id=GROUP_ID,
                owner_id=OWNER_ID,
                bot_id="620000000099@s.whatsapp.net",
                ttl_seconds=86_400,
            )
        )
        result = controller.observe_group_message(
            {
                "chat_id": GROUP_ID,
                "sender": "620000000002@s.whatsapp.net",
                "text": "Rapat koordinasi proyek besok, tindak lanjut dibagi hari ini.",
                "mentions_bot": False,
                "received_at": 100,
            }
        )
        self.assertEqual(result["status"], "buffered")
        self.assertEqual(controller._events, [{"topics": ("Rapat", "Tindak lanjut"), "received_at": 100}])

        response = controller.handle_owner_dm(
            {"sender": OWNER_ID, "text": "rangkuman grup hari ini", "received_at": 86_499}
        )
        self.assertEqual(response["status"], "summary_ready")
        self.assertEqual(response["outbound"]["recipient"], OWNER_ID)
        self.assertIn("Rapat", response["outbound"]["body"])
        self.assertIn("Tindak lanjut", response["outbound"]["body"])

    def test_daily_metadata_expires_at_24_hour_boundary(self):
        controller = pilot_core.PilotController(
            pilot_core.PilotPolicy(
                group_id=GROUP_ID,
                owner_id=OWNER_ID,
                bot_id="620000000099@s.whatsapp.net",
                ttl_seconds=86_400,
            )
        )
        controller.observe_group_message(
            {
                "chat_id": GROUP_ID,
                "sender": "620000000002@s.whatsapp.net",
                "text": "Deadline proposal hari ini",
                "mentions_bot": False,
                "received_at": 100,
            }
        )
        response = controller.handle_owner_dm(
            {"sender": OWNER_ID, "text": "ringkas", "received_at": 86_500}
        )
        self.assertEqual(response["status"], "summary_empty")
        self.assertIsNone(response["outbound"])


if __name__ == "__main__":
    unittest.main()
