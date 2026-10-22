import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "x_group_summary_plugin"))
import group_summary


GROUP_ID = "120000000000001@g.us"
GROUP_ID_2 = "120000000000002@g.us"
OWNER_ID = "620000000001@s.whatsapp.net"


def event(*, chat_type, chat_id, user_id, text, media=False):
    return SimpleNamespace(
        text=text,
        message_type="photo" if media else "text",
        media_urls=["synthetic"] if media else [],
        media_types=["image/jpeg"] if media else [],
        source=SimpleNamespace(platform=SimpleNamespace(value="whatsapp"), chat_type=chat_type, chat_id=chat_id, user_id=user_id),
    )


class GatewayGroupSummaryHookTests(unittest.TestCase):
    def setUp(self):
        self.policy = group_summary.Policy(
            group_ids=frozenset({GROUP_ID}),
            owner_id=OWNER_ID,
            ttl_seconds=86_400,
        )
        self.hook = group_summary.GroupSummaryHook(self.policy, now=lambda: 100.0)

    def test_allowlisted_group_text_is_consumed_without_model_dispatch(self):
        result = asyncio.run(self.hook.handle(event(
            chat_type="group", chat_id=GROUP_ID, user_id="620000000002@s.whatsapp.net",
            text="Rapat proyek besok; deadline revisi hari ini.",
        )))
        self.assertEqual(result, {"action": "skip", "reason": "x_group_summary_observed"})
        self.assertEqual(self.hook.records, [{"at": 100.0, "topics": ("Deadline", "Rapat")}])

    def test_second_allowlisted_group_is_consumed_without_model_dispatch(self):
        policy = group_summary.Policy(group_ids=frozenset({GROUP_ID, GROUP_ID_2}), owner_id=OWNER_ID, ttl_seconds=86_400)
        hook = group_summary.GroupSummaryHook(policy, now=lambda: 100.0)
        result = asyncio.run(hook.handle(event(
            chat_type="group", chat_id=GROUP_ID_2, user_id="620000000002@s.whatsapp.net",
            text="Tindak lanjut tugas dibagi.",
        )))
        self.assertEqual(result, {"action": "skip", "reason": "x_group_summary_observed"})
        self.assertEqual(hook.records, [{"at": 100.0, "topics": ("Tindak lanjut",)}])

    def test_group_media_is_consumed_without_retention_or_dispatch(self):
        result = asyncio.run(self.hook.handle(event(
            chat_type="group", chat_id=GROUP_ID, user_id="620000000002@s.whatsapp.net",
            text="foto", media=True,
        )))
        self.assertEqual(result, {"action": "skip", "reason": "x_group_summary_media_dropped"})
        self.assertEqual(self.hook.records, [])

    def test_owner_summary_request_is_rewritten_with_metadata_not_raw_text(self):
        asyncio.run(self.hook.handle(event(
            chat_type="group", chat_id=GROUP_ID, user_id="620000000002@s.whatsapp.net",
            text="Rapat proyek rahasia besok.",
        )))
        owner_event = event(chat_type="dm", chat_id=OWNER_ID, user_id=OWNER_ID, text="tolong rangkum grup hari ini")
        result = asyncio.run(self.hook.handle(owner_event))
        self.assertEqual(result["action"], "rewrite")
        self.assertIn("Rapat", result["text"])
        self.assertNotIn("rahasia", result["text"].lower())
        self.assertIn("jangan mengaku membaca teks mentah", result["text"])

    def test_non_owner_summary_request_is_not_rewritten(self):
        result = asyncio.run(self.hook.handle(event(
            chat_type="dm", chat_id="620000000003@s.whatsapp.net", user_id="620000000003@s.whatsapp.net",
            text="rangkum grup hari ini",
        )))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
