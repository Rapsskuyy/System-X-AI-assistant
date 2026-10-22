"""Audit lokal fail-closed atas skema dummy; bukan pembaca status efektif adapter Hermes."""
import argparse
import json
import os
from pathlib import Path
from typing import Any

FIELDS = (
    "config_readable", "pilot_enabled", "send_enabled", "group_count",
    "owner_configured", "dm_owner_only", "require_mention", "media_enabled",
    "url_preview_enabled", "kill_switch_configured", "group_tool_execution_enabled",
    "raw_message_logging_enabled", "group_auto_reply_enabled",
    "temporary_group_summary_buffer_enabled", "summary_delivery_policy",
    "retention_mode", "gateway_start_enabled", "runtime_isolation_status",
)
MAX_BYTES = 1024 * 1024


def unknown_report():
    report: dict[str, Any] = {key: None for key in FIELDS}
    report["config_readable"] = False
    report["runtime_isolation_status"] = "BELUM_DIUJI"
    return report


def explicit_bool(mapping, key):
    value = mapping.get(key)
    return value if type(value) is bool else None


def canonical_id(value, suffix):
    return isinstance(value, str) and value.endswith(suffix) and bool(value[: -len(suffix)].strip())


def bot_number_valid(value):
    return isinstance(value, str) and value.startswith("+") and value[1:].isdigit() and 8 <= len(value[1:]) <= 15


def audit_text(text):
    report = unknown_report()
    try:
        from ruamel.yaml import YAML
        parser = YAML(typ="safe", pure=True)
        parser.allow_duplicate_keys = False
        data = parser.load(text)
    except Exception:
        return report
    if not isinstance(data, dict):
        return report
    report["config_readable"] = True
    pilot = data.get("x_wa_pilot_audit")
    if not isinstance(pilot, dict):
        return report

    report["send_enabled"] = explicit_bool(pilot, "send_enabled")
    groups = pilot.get("allowlisted_groups")
    if isinstance(groups, list) and all(canonical_id(item, "@g.us") for item in groups):
        report["group_count"] = len(groups)
    owner = pilot.get("owner_id")
    if isinstance(owner, str):
        report["owner_configured"] = canonical_id(owner, "@s.whatsapp.net")
    dm_sender_policy = pilot.get("dm_sender_policy", pilot.get("sender_policy"))
    if isinstance(dm_sender_policy, str):
        report["dm_owner_only"] = dm_sender_policy == "owner_only"
    report["require_mention"] = explicit_bool(pilot, "require_mention")
    media = explicit_bool(pilot, "media_enabled")
    attachments = explicit_bool(pilot, "attachments_enabled")
    if media is True or attachments is True:
        report["media_enabled"] = True
    elif media is False and attachments is False:
        report["media_enabled"] = False
    report["url_preview_enabled"] = explicit_bool(pilot, "url_preview_enabled")
    kill_configured = explicit_bool(pilot, "kill_switch_configured")
    kill_active = explicit_bool(pilot, "kill_switch_active")
    if kill_configured is True and kill_active is True:
        report["kill_switch_configured"] = True
    elif kill_configured is False or kill_active is False:
        report["kill_switch_configured"] = False
    report["group_tool_execution_enabled"] = explicit_bool(pilot, "group_tool_execution_enabled")
    report["raw_message_logging_enabled"] = explicit_bool(pilot, "raw_message_logging_enabled")
    report["group_auto_reply_enabled"] = explicit_bool(pilot, "group_auto_reply_enabled")
    report["temporary_group_summary_buffer_enabled"] = explicit_bool(pilot, "temporary_group_summary_buffer_enabled")
    summary_delivery_policy = pilot.get("summary_delivery_policy")
    if summary_delivery_policy == "owner_dm_on_request":
        report["summary_delivery_policy"] = summary_delivery_policy
    retention_mode = pilot.get("retention_mode")
    if retention_mode == "metadata_only":
        report["retention_mode"] = retention_mode
    report["gateway_start_enabled"] = explicit_bool(pilot, "gateway_start_enabled")

    common_controls = (
        explicit_bool(pilot, "enabled") is True,
        bot_number_valid(pilot.get("bot_number")),
        report["owner_configured"] is True,
        report["send_enabled"] is False,
        report["media_enabled"] is False,
        report["url_preview_enabled"] is False,
        report["kill_switch_configured"] is True,
        report["group_tool_execution_enabled"] is False,
        report["raw_message_logging_enabled"] is False,
        explicit_bool(pilot, "default_deny") is True,
    )
    dm_only_controls = (
        pilot.get("group_policy") == "disabled",
        report["group_count"] == 0,
        pilot.get("ttl_seconds") == 60,
        report["dm_owner_only"] is True,
        pilot.get("unauthorized_sender_behavior") == "reject",
    )
    group_controls = (
        pilot.get("group_policy") == "allowlist",
        report["group_count"] in (1, 2),
        report["dm_owner_only"] is True,
        pilot.get("unauthorized_sender_behavior") == "reject",
        report["require_mention"] is False,
        pilot.get("ttl_seconds") == 86_400,
        report["retention_mode"] == "metadata_only",
        report["group_auto_reply_enabled"] is False,
        report["temporary_group_summary_buffer_enabled"] is True,
        report["summary_delivery_policy"] == "owner_dm_on_request",
        report["gateway_start_enabled"] is False,
    )
    report["pilot_enabled"] = True if all(common_controls) and (all(dm_only_controls) or all(group_controls)) else None
    return report


def audit_file(path):
    try:
        source = Path(path)
        if source.is_symlink() or not source.is_file() or source.stat().st_size > MAX_BYTES:
            return unknown_report()
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return unknown_report()
    return audit_text(text)


def render(report):
    return json.dumps({key: report[key] for key in FIELDS}, separators=(",", ":"))


def ready(report):
    # Kontrak dummy tidak pernah membuktikan isolasi runtime atau konfigurasi efektif Hermes.
    return False


def main(argv=None):
    cli = argparse.ArgumentParser(description="Validator read-only untuk skema audit dummy pilot.")
    cli.add_argument("--config", type=Path, help="YAML lokal; default: HERMES_HOME/config.yaml")
    args = cli.parse_args(argv)
    home = os.environ.get("HERMES_HOME")
    path = args.config if args.config is not None else (Path(home) / "config.yaml" if home else None)
    report = audit_file(path) if path is not None else unknown_report()
    print(render(report))
    return 2  # TERBLOKIR: tidak ada verifikasi konfigurasi efektif/runtime.


if __name__ == "__main__":
    raise SystemExit(main())
