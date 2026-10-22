#!/usr/bin/env python3
"""Simulator lokal X tahap 1. Hanya memproses data sintetis."""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DELIVERY_PATH_ENABLED = False
DELIVERY_CAPABILITIES = frozenset()
CONTENT_POLICY = {
    "media_download": False,
    "attachment_processing": False,
    "url_preview": False,
}


class SyntheticTTLBuffer:
    """Buffer RAM sintetis yang menghapus entri saat TTL tercapai."""
    def __init__(self, ttl_seconds):
        self.ttl_seconds = ttl_seconds
        self._records = []

    def add(self, record, now_seconds):
        self._records.append({"record": record, "expires_at": now_seconds + self.ttl_seconds})

    def expire(self, now_seconds):
        self._records = [entry for entry in self._records if entry["expires_at"] > now_seconds]

    def count(self, now_seconds):
        self.expire(now_seconds)
        return len(self._records)

    def clear(self):
        removed = len(self._records)
        self._records.clear()
        return removed


class SyntheticReadOnlyObserver:
    """Stub lokal: hanya menerima event sintetis dan mengembalikan data tereduksi."""
    capabilities = frozenset({"observe_event"})

    def __init__(self, allowlist):
        self._allowlist = allowlist

    def observe_event(self, event, kill_switch_active=False):
        outcome = process_group_message(event, self._allowlist, kill_switch_active)
        return {
            "status": outcome["status"],
            "notifications": outcome["notifications"],
            "reminders": outcome["reminders"],
            "media_decision": "not_downloaded",
            "attachment_decision": "not_processed",
            "url_preview_decision": "disabled",
        }


def isolated_observer_payload(allowlist, event):
    """Batas subprocess lokal: hanya serialisasi keputusan observer yang sudah disanitasi."""
    return json.dumps(SyntheticReadOnlyObserver(allowlist).observe_event(event), sort_keys=True)


def local_security_posture():
    """Pernyataan ruang lingkup simulator lokal, bukan kontrol OS produksi."""
    return {
        "dependencies": "stdlib_only",
        "session_storage": "disabled",
        "filesystem": "read_only_synthetic_fixtures",
        "network": "disabled",
    }


def classify_topic(text):
    text = text.lower()
    if "ringkas" in text or "rangkuman" in text:
        return "Ringkasan"
    if "reminder" in text or "ingatkan" in text:
        return "Reminder"
    return "Lainnya"


def create_reminder_from_text(text, source):
    """Hitung waktu reminder dari waktu acara, bukan waktu pesan masuk."""
    match = re.search(r"\bjam\s*(\d{1,2})(?::(\d{2}))?", text.lower())
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2) or 0)
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return None
    offset_match = re.search(r"(\d+)\s*menit\s*(?:sebelumnya|lebih awal)", text.lower())
    offset = int(offset_match.group(1)) if offset_match else 0
    meeting = datetime(2000, 1, 1, hour, minute)
    reminder = meeting - timedelta(minutes=offset)
    return {"source": source, "meeting_time": meeting.strftime("%H:%M"), "offset_minutes": offset, "reminder_time": reminder.strftime("%H:%M")}


def process_group_message(message, allowlist, kill_switch_active=False):
    """Observasi pasif: pesan grup tidak pernah menjalankan tool atau terminal."""
    if kill_switch_active:
        return {"status": "blocked_kill_switch", "notifications": [], "reminders": [], "actions": [], "tool_execution_requested": False}
    if allowlist is None:
        return {"status": "blocked_allowlist_unavailable", "notifications": [], "reminders": [], "actions": [], "tool_execution_requested": False}
    if message.get("group") not in allowlist.get("groups_allowlist", []):
        return {"status": "ignored_not_allowlisted", "notifications": [], "reminders": [], "actions": [], "tool_execution_requested": False}
    notifications, reminders = [], []
    if message.get("mentions_x"):
        topic = classify_topic(message.get("text", ""))
        notifications.append({"time": message.get("time"), "group": message.get("group"), "topic": topic, "decision": "notification_queued"})
        if topic == "Reminder":
            reminder = create_reminder_from_text(message.get("text", ""), message.get("group"))
            if reminder:
                reminders.append(reminder)
    return {"status": "observed", "notifications": notifications, "reminders": reminders, "actions": [], "tool_execution_requested": False}


def build_summary(messages):
    mentions = sum(1 for message in messages if message.get("mentions_x"))
    return f"Rangkuman sintetis: {len(messages)} pesan allowlist, {mentions} mention X."


def resolve_memory_opt_in(answer, synthetic_summary):
    """Contoh memori hanya berada di RAM dan tidak pernah ditulis ke disk."""
    if answer.strip().lower() != "ya":
        return None
    return {"synthetic_only": True, "summary": synthetic_summary, "note": "Contoh opt-in lokal; hilang saat proses selesai."}


def process_owner_dm(dm, allowlist, observed_messages):
    """Hanya owner_dm pada allowlist yang dapat meminta fitur owner."""
    if dm.get("sender") != allowlist.get("owner_dm"):
        return {"status": "ignored_not_owner", "response": None, "reminder": None, "memory": None}
    text = dm.get("text", "")
    normalized = text.lower()
    if "simpan" in normalized and ("ringkasan" in normalized or "rangkuman" in normalized):
        return {"status": "owner_memory_saved_simulated", "response": "Opt-in memori sintetis diterima.", "reminder": None, "memory": resolve_memory_opt_in("ya", build_summary(observed_messages))}
    if "reminder" in normalized or "ingatkan" in normalized:
        reminder = create_reminder_from_text(text, "DM owner")
        return {"status": "owner_reminder", "response": "Reminder sintetis dibuat." if reminder else "Waktu reminder tidak ditemukan.", "reminder": reminder, "memory": None}
    if "ringkas" in normalized or "rangkuman" in normalized:
        return {"status": "owner_summary", "response": build_summary(observed_messages), "reminder": None, "memory": None}
    return {"status": "owner_no_action", "response": None, "reminder": None, "memory": None}


def load_allowlist(path):
    """Muat allowlist lokal; setiap kegagalan konfigurasi menghasilkan deny."""
    try:
        with Path(path).open(encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("groups_allowlist"), list) or not isinstance(data.get("owner_dm"), str):
        return None
    return data


def load_synthetic_data():
    allowlist = load_allowlist(BASE_DIR / "data" / "allowlist.json")
    with (BASE_DIR / "data" / "synthetic_messages.json").open(encoding="utf-8") as file:
        messages = json.load(file)
    return allowlist, messages


def run_simulation(memory_answer="tidak"):
    allowlist, messages = load_synthetic_data()
    if allowlist is None:
        return {"allowlist": None, "observed": [], "notifications": [], "reminders": [], "ignored_groups": 0, "owner_results": [], "memory": None, "status": "blocked_allowlist_unavailable"}
    observed, notifications, reminders, ignored = [], [], [], 0
    buffer = SyntheticTTLBuffer(ttl_seconds=60)
    for index, message in enumerate(messages):
        outcome = process_group_message(message, allowlist)
        if outcome["status"] == "ignored_not_allowlisted":
            ignored += 1
        else:
            observed.append(message)
            notifications.extend(outcome["notifications"])
            reminders.extend(outcome["reminders"])
            for notification in outcome["notifications"]:
                buffer.add(notification, now_seconds=index)
    owner_dms = [
        {"sender": allowlist["owner_dm"], "text": "minta rangkuman"},
        {"sender": allowlist["owner_dm"], "text": "Buat reminder Meeting jam 14, 10 menit sebelumnya."},
        {"sender": allowlist["owner_dm"], "text": "simpan ringkasan"},
    ]
    owner_results = [process_owner_dm(dm, allowlist, observed) for dm in owner_dms]
    owner_decisions = [{"status": item["status"], "reminder_time": item["reminder"]["reminder_time"] if item["reminder"] else None} for item in owner_results]
    memory = resolve_memory_opt_in(memory_answer, build_summary(observed))
    observed_count = len(observed)
    observed.clear()
    owner_results.clear()
    messages.clear()
    buffer.clear()
    return {"allowlist": allowlist, "observed_count": observed_count, "notifications": notifications, "reminders": reminders, "ignored_groups": ignored, "owner_decisions": owner_decisions, "memory": memory, "transient_buffer_entries_after_cleanup": buffer.count(now_seconds=60), "status": "ok"}


def format_demo(result):
    """Render output tereduksi; tidak pernah mencetak teks pesan/DM mentah."""
    lines = ["=== SIMULASI X (LOKAL, DATA SINTETIS) ===", f"status={result['status']}", f"event_allowlisted={result['observed_count']} decision=observed", f"event_ignored={result['ignored_groups']} decision=ignored_not_allowlisted"]
    for item in result["notifications"]:
        lines.append(f"time={item['time']} group={item['group']} category={item['topic']} decision={item['decision']}")
    for item in result["reminders"]:
        lines.append(f"group={item['source']} category=Reminder decision=reminder_created event_time={item['meeting_time']} reminder_time={item['reminder_time']}")
    for item in result["owner_decisions"]:
        suffix = f" reminder_time={item['reminder_time']}" if item["reminder_time"] else ""
        lines.append(f"category=OwnerDM decision={item['status']}{suffix}")
    memory_decision = "not_saved" if result["memory"] is None else "synthetic_opt_in_ram_only"
    lines.append(f"category=Memory decision={memory_decision}")
    lines.append(f"category=Buffer decision=cleared entries={result['transient_buffer_entries_after_cleanup']}")
    lines.append("external_connections=disabled")
    return "\n".join(lines)


def main():
    print(format_demo(run_simulation(memory_answer="tidak")))


if __name__ == "__main__":
    main()