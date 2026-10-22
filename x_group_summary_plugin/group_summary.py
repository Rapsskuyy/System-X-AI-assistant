"""Silent one-group WhatsApp summary interceptor for Hermes gateway.

The hook consumes allowlisted group messages before authorization/model dispatch.
It retains only derived topic labels in memory for 24 hours and rewrites an
owner-DM summary request into a metadata-backed model prompt.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import time
from typing import Any, Callable


_SUMMARY_REQUEST = re.compile(r"\b(ringkas|rangkum(?:an)?)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Policy:
    group_ids: frozenset[str]
    owner_id: str
    ttl_seconds: int = 86_400


def _valid_jid(value: object, suffix: str) -> bool:
    return isinstance(value, str) and value.endswith(suffix) and value[: -len(suffix)].isdigit()


def load_policy(path: str | os.PathLike[str]) -> Policy:
    """Load only the approved one-group, metadata-only pilot manifest."""
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("policy manifest is unavailable")
    from ruamel.yaml import YAML

    parser = YAML(typ="safe", pure=True)
    parser.allow_duplicate_keys = False
    data = parser.load(source.read_text(encoding="utf-8"))
    pilot = data.get("x_wa_pilot_audit") if isinstance(data, dict) else None
    if not isinstance(pilot, dict):
        raise ValueError("policy manifest has no pilot block")
    groups = pilot.get("allowlisted_groups")
    owner_id = pilot.get("owner_id")
    valid_groups = isinstance(groups, list) and 1 <= len(groups) <= 5 and len(groups) == len(set(groups)) and all(_valid_jid(item, "@g.us") for item in groups)
    required = (
        pilot.get("group_policy") == "allowlist",
        pilot.get("require_mention") is False,
        pilot.get("ttl_seconds") == 86_400,
        pilot.get("retention_mode") == "metadata_only",
        pilot.get("group_auto_reply_enabled") is False,
        pilot.get("summary_delivery_policy") == "owner_dm_on_request",
        valid_groups,
        _valid_jid(owner_id, "@s.whatsapp.net"),
    )
    if not all(required) or not isinstance(owner_id, str) or not isinstance(groups, list):
        raise ValueError("policy manifest does not satisfy silent metadata-only group policy")
    return Policy(group_ids=frozenset(str(group) for group in groups), owner_id=owner_id)


def _topics(text: str) -> tuple[str, ...]:
    normalized = text.lower()
    result: list[str] = []
    if "deadline" in normalized:
        result.append("Deadline")
    if any(word in normalized for word in ("rapat", "meeting")):
        result.append("Rapat")
    if any(word in normalized for word in ("tugas", "aksi", "todo", "tindak lanjut")):
        result.append("Tindak lanjut")
    return tuple(result) or ("Topik umum",)


class GroupSummaryHook:
    def __init__(self, policy: Policy, now: Callable[[], float] = time.time):
        self.policy = policy
        self._now = now
        self.records: list[dict[str, Any]] = []

    def _expire(self, now: float) -> None:
        cutoff = now - self.policy.ttl_seconds
        self.records[:] = [item for item in self.records if item["at"] > cutoff]

    def _is_owner_dm(self, source: Any) -> bool:
        return (
            getattr(source, "chat_type", None) == "dm"
            and (getattr(source, "user_id", None) == self.policy.owner_id or getattr(source, "chat_id", None) == self.policy.owner_id)
        )

    def _summary_prompt(self) -> str:
        labels: list[str] = []
        for record in self.records:
            for label in record["topics"]:
                if label not in labels:
                    labels.append(label)
        topic_text = ", ".join(labels) if labels else "belum ada aktivitas teks yang tercatat"
        return (
            "Jawab dalam Bahasa Indonesia. Buat rangkuman ringkas dari observasi grup 24 jam terakhir. "
            "Data interceptor tepercaya: jumlah pesan teks=%d; topik=%s. "
            "jangan mengaku membaca teks mentah, jangan mengarang detail, nama, keputusan, atau kutipan. "
            "Sampaikan bahwa ini rangkuman metadata bila informasinya terbatas."
        ) % (len(self.records), topic_text)

    async def handle(self, event: Any, **_kwargs: Any) -> dict[str, str] | None:
        source = getattr(event, "source", None)
        platform = getattr(getattr(source, "platform", None), "value", None)
        if platform != "whatsapp":
            return None
        if getattr(source, "chat_type", None) == "group" and getattr(source, "chat_id", None) in self.policy.group_ids:
            if getattr(event, "media_urls", None) or getattr(event, "media_types", None) or getattr(event, "message_type", None) != "text":
                return {"action": "skip", "reason": "x_group_summary_media_dropped"}
            text = getattr(event, "text", None)
            if not isinstance(text, str):
                return {"action": "skip", "reason": "x_group_summary_invalid_text"}
            now = self._now()
            self._expire(now)
            self.records.append({"at": now, "topics": _topics(text)})
            return {"action": "skip", "reason": "x_group_summary_observed"}
        if self._is_owner_dm(source) and isinstance(getattr(event, "text", None), str) and _SUMMARY_REQUEST.search(event.text):
            self._expire(self._now())
            return {"action": "rewrite", "text": self._summary_prompt()}
        return None


def register(ctx: Any) -> None:
    manifest_path = os.environ.get("X_GROUP_SUMMARY_POLICY_PATH", "").strip()
    if not manifest_path:
        return
    try:
        hook = GroupSummaryHook(load_policy(manifest_path))
    except Exception:
        return
    ctx.register_hook("pre_gateway_dispatch", hook.handle)
