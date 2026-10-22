"""Core pilot X tanpa koneksi WhatsApp, pairing, atau pengiriman nyata.

Adapter WhatsApp nantinya hanya boleh meneruskan event tereduksi ke modul ini dan
mengeksekusi outbound intent setelah gateway disetujui secara terpisah.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class PilotPolicy:
    group_id: str
    owner_id: str
    bot_id: str
    ttl_seconds: int = 60


class PilotController:
    """Pemrosesan murni dan sementara untuk pilot satu grup allowlist."""

    def __init__(self, policy: PilotPolicy):
        self.policy = policy
        self._events: list[dict[str, Any]] = []

    def observe_group_message(self, event: dict[str, Any]) -> dict[str, str]:
        """Amati semua teks grup allowlist; buffer menyimpan metadata, bukan teks mentah."""
        if event.get("chat_id") != self.policy.group_id:
            return {"status": "ignored_not_allowlisted"}
        text = event.get("text")
        received_at = event.get("received_at")
        if not isinstance(text, str) or not isinstance(received_at, (int, float)):
            return {"status": "ignored_invalid_event"}
        self._expire(received_at)
        self._events.append({"topics": self._topics_from_text(text), "received_at": received_at})
        return {"status": "buffered"}

    def handle_owner_dm(self, dm: dict[str, Any]) -> dict[str, Any]:
        """Buat intent ringkasan/reminder untuk owner; tidak pernah mengirim pesan."""
        if dm.get("sender") != self.policy.owner_id:
            return {"status": "ignored_not_owner", "outbound": None}
        text = dm.get("text")
        received_at = dm.get("received_at")
        if not isinstance(text, str) or not isinstance(received_at, (int, float)):
            return {"status": "ignored_invalid_command", "outbound": None}
        self._expire(received_at)
        normalized = text.lower()
        if "ringkas" in normalized or "rangkuman" in normalized:
            body = self._summary_body()
            if body is None:
                return {"status": "summary_empty", "outbound": None}
            return {
                "status": "summary_ready",
                "outbound": {"recipient": self.policy.owner_id, "kind": "summary", "body": body},
            }
        if "ingatkan" in normalized or "reminder" in normalized:
            scheduled_for = self._reminder_time(text)
            if scheduled_for is None:
                return {"status": "reminder_time_missing", "outbound": None}
            return {
                "status": "reminder_ready",
                "outbound": {
                    "recipient": self.policy.owner_id,
                    "kind": "reminder",
                    "scheduled_for": scheduled_for,
                    "body": f"Reminder untuk {scheduled_for} sudah disiapkan.",
                },
            }
        return {"status": "owner_no_action", "outbound": None}

    def _expire(self, now: float) -> None:
        cutoff = now - self.policy.ttl_seconds
        self._events = [event for event in self._events if event["received_at"] > cutoff]

    def _summary_body(self) -> str | None:
        if not self._events:
            return None
        topics: list[str] = []
        for event in self._events:
            for topic in event["topics"]:
                if topic not in topics:
                    topics.append(topic)
        if not topics:
            topics.append("Topik umum")
        return f"Rangkuman grup (sementara): {len(self._events)} pesan diproses. Topik: {', '.join(topics)}."

    @staticmethod
    def _topics_from_text(text: str) -> tuple[str, ...]:
        normalized = text.lower()
        topics: list[str] = []
        if "deadline" in normalized:
            topics.append("Deadline")
        if any(word in normalized for word in ("rapat", "meeting")):
            topics.append("Rapat")
        if any(word in normalized for word in ("tugas", "aksi", "todo", "tindak lanjut")):
            topics.append("Tindak lanjut")
        return tuple(topics) or ("Topik umum",)

    @staticmethod
    def _reminder_time(text: str) -> str | None:
        time_match = re.search(r"\bjam\s*(\d{1,2})(?::(\d{2}))?", text.lower())
        if not time_match:
            return None
        hour, minute = int(time_match.group(1)), int(time_match.group(2) or 0)
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            return None
        offset_match = re.search(r"(\d+)\s*menit\s*(?:sebelumnya|lebih awal)", text.lower())
        offset = int(offset_match.group(1)) if offset_match else 0
        total_minutes = (hour * 60 + minute - offset) % (24 * 60)
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
