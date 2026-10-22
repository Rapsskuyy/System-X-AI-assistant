"""Prompt lokal tanpa echo untuk membuat manifest pilot proyek; tidak menyentuh Hermes."""
import argparse
import getpass
import io
import json
import sys
from pathlib import Path

from ruamel.yaml import YAML

import validator

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "pilot.local.yaml"
BOT_FORMAT_ERROR = "Nomor bot tidak valid: gunakan + diikuti 8–15 digit tanpa spasi."
OWNER_FORMAT_ERROR = "ID owner tidak valid: gunakan angka internasional tanpa + lalu @s.whatsapp.net."


def owner_id_valid(value):
    suffix = "@s.whatsapp.net"
    if not isinstance(value, str) or not value.endswith(suffix):
        return False
    number = value[:-len(suffix)]
    return number.isdigit() and 8 <= len(number) <= 15


def group_id_valid(value):
    suffix = "@g.us"
    if not isinstance(value, str) or not value.endswith(suffix):
        return False
    identifier = value[:-len(suffix)]
    return identifier.isdigit() and 8 <= len(identifier) <= 24


def build_manifest(bot_number, owner_id):
    if not validator.bot_number_valid(bot_number):
        raise ValueError(BOT_FORMAT_ERROR)
    if not owner_id_valid(owner_id):
        raise ValueError(OWNER_FORMAT_ERROR)
    return {
        "x_wa_pilot_audit": {
            "enabled": True,
            "bot_number": bot_number,
            "send_enabled": False,
            "group_policy": "disabled",
            "allowlisted_groups": [],
            "owner_id": owner_id,
            "sender_policy": "owner_only",
            "unauthorized_sender_behavior": "reject",
            "media_enabled": False,
            "attachments_enabled": False,
            "url_preview_enabled": False,
            "kill_switch_configured": True,
            "kill_switch_active": True,
            "ttl_seconds": 60,
            "group_tool_execution_enabled": False,
            "raw_message_logging_enabled": False,
            "default_deny": True,
        }
    }


def build_one_group_manifest(bot_number, owner_id, group_id):
    if not validator.bot_number_valid(bot_number):
        raise ValueError(BOT_FORMAT_ERROR)
    if not owner_id_valid(owner_id):
        raise ValueError(OWNER_FORMAT_ERROR)
    if not group_id_valid(group_id):
        raise ValueError("ID grup tidak valid: gunakan satu ID @g.us.")
    return {
        "x_wa_pilot_audit": {
            "enabled": True,
            "bot_number": bot_number,
            "send_enabled": False,
            "group_policy": "allowlist",
            "allowlisted_groups": [group_id],
            "require_mention": False,
            "owner_id": owner_id,
            "dm_sender_policy": "owner_only",
            "unauthorized_sender_behavior": "reject",
            "media_enabled": False,
            "attachments_enabled": False,
            "url_preview_enabled": False,
            "kill_switch_configured": True,
            "kill_switch_active": True,
            "ttl_seconds": 86_400,
            "retention_mode": "metadata_only",
            "group_tool_execution_enabled": False,
            "raw_message_logging_enabled": False,
            "group_auto_reply_enabled": False,
            "temporary_group_summary_buffer_enabled": True,
            "summary_delivery_policy": "owner_dm_on_request",
            "gateway_start_enabled": False,
            "default_deny": True,
        }
    }


def build_two_group_manifest(bot_number, owner_id, group_ids):
    if not validator.bot_number_valid(bot_number):
        raise ValueError(BOT_FORMAT_ERROR)
    if not owner_id_valid(owner_id):
        raise ValueError(OWNER_FORMAT_ERROR)
    if not isinstance(group_ids, list) or len(group_ids) != 2 or len(set(group_ids)) != 2 or not all(group_id_valid(group_id) for group_id in group_ids):
        raise ValueError("ID grup tidak valid: masukkan tepat dua ID @g.us yang berbeda, dipisahkan koma.")
    return {
        "x_wa_pilot_audit": {
            "enabled": True,
            "bot_number": bot_number,
            "send_enabled": False,
            "group_policy": "allowlist",
            "allowlisted_groups": group_ids,
            "require_mention": False,
            "owner_id": owner_id,
            "dm_sender_policy": "owner_only",
            "unauthorized_sender_behavior": "reject",
            "media_enabled": False,
            "attachments_enabled": False,
            "url_preview_enabled": False,
            "kill_switch_configured": True,
            "kill_switch_active": True,
            "ttl_seconds": 86_400,
            "retention_mode": "metadata_only",
            "group_tool_execution_enabled": False,
            "raw_message_logging_enabled": False,
            "group_auto_reply_enabled": False,
            "temporary_group_summary_buffer_enabled": True,
            "summary_delivery_policy": "owner_dm_on_request",
            "gateway_start_enabled": False,
            "default_deny": True,
        }
    }


def dump_yaml(manifest):
    yaml = YAML()
    yaml.default_flow_style = False
    stream = io.StringIO()
    yaml.dump(manifest, stream)
    return stream.getvalue()


def print_reduced_status(report, stream=sys.stdout):
    print(validator.render(report), file=stream)


def load_existing_identifiers(source_path):
    source = Path(source_path)
    try:
        if source.is_symlink() or not source.is_file():
            return None
        yaml = YAML(typ="safe", pure=True)
        yaml.allow_duplicate_keys = False
        data = yaml.load(source.read_text(encoding="utf-8"))
        pilot = data.get("x_wa_pilot_audit") if isinstance(data, dict) else None
        if not isinstance(pilot, dict):
            return None
        bot, owner = pilot.get("bot_number"), pilot.get("owner_id")
        if not validator.bot_number_valid(bot) or not owner_id_valid(owner):
            return None
        return bot, owner
    except (OSError, UnicodeError, ValueError):
        return None


def main_one_group(input_fn=None, source_path=None, output_path=None, stream=None):
    input_fn = input_fn or getpass.getpass
    source_path = Path(source_path) if source_path is not None else DEFAULT_OUTPUT
    output_path = Path(output_path) if output_path is not None else source_path.with_name("pilot.one-group.local.yaml")
    stream = stream or sys.stdout
    identifiers = load_existing_identifiers(source_path)
    if identifiers is None:
        print("TERBLOKIR: manifest sumber lokal tidak valid atau tidak tersedia.", file=stream)
        return 2
    print("Input lokal tanpa echo. Masukkan satu ID grup; jangan masukkan OTP, QR, token, secret, atau file sesi.", file=stream)
    group_id = input_fn("ID grup @g.us: ").strip()
    try:
        manifest = build_one_group_manifest(*identifiers, group_id)
        yaml_text = dump_yaml(manifest)
        report = validator.audit_text(yaml_text)
        if output_path.exists() or output_path.is_symlink():
            print("TERBLOKIR: manifest satu-grup sudah ada; tidak ditimpa.", file=stream)
            return 2
        output_path.write_text(yaml_text, encoding="utf-8")
    except (OSError, ValueError):
        print("TERBLOKIR: satu ID grup @g.us yang valid diperlukan; tidak ada manifest dibuat.", file=stream)
        return 2
    finally:
        group_id = ""

    print_reduced_status(report, stream=stream)
    print("KONFIGURASI_TEREDUKSI_DITAMPILKAN; gateway tetap nonaktif dan tidak dijalankan.", file=stream)
    return 0


def main_two_groups(input_fn=None, source_path=None, output_path=None, stream=None):
    input_fn = input_fn or getpass.getpass
    source_path = Path(source_path) if source_path is not None else DEFAULT_OUTPUT
    output_path = Path(output_path) if output_path is not None else source_path.with_name("pilot.two-group.local.yaml")
    stream = stream or sys.stdout
    identifiers = load_existing_identifiers(source_path)
    if identifiers is None:
        print("TERBLOKIR: manifest sumber lokal tidak valid atau tidak tersedia.", file=stream)
        return 2
    print("Input lokal tanpa echo. Masukkan tepat dua ID grup; jangan masukkan OTP, QR, token, secret, atau file sesi.", file=stream)
    supplied = input_fn("Dua ID grup @g.us (pisahkan dengan koma): ").strip()
    group_ids = [item.strip() for item in supplied.split(",")]
    try:
        manifest = build_two_group_manifest(*identifiers, group_ids)
        yaml_text = dump_yaml(manifest)
        report = validator.audit_text(yaml_text)
        if output_path.exists() or output_path.is_symlink():
            print("TERBLOKIR: manifest dua-grup sudah ada; tidak ditimpa.", file=stream)
            return 2
        output_path.write_text(yaml_text, encoding="utf-8")
    except (OSError, ValueError):
        print("TERBLOKIR: tepat dua ID grup @g.us yang berbeda diperlukan; tidak ada manifest dibuat.", file=stream)
        return 2
    finally:
        supplied = ""
        group_ids = []

    print_reduced_status(report, stream=stream)
    print("KONFIGURASI_TEREDUKSI_DITAMPILKAN; gateway tetap nonaktif dan tidak dijalankan.", file=stream)
    return 0


def main(input_fn=None, output_path=None, stream=None):
    input_fn = input_fn or getpass.getpass
    output_path = Path(output_path) if output_path is not None else DEFAULT_OUTPUT
    stream = stream or sys.stdout
    print("Input lokal tanpa echo. Jangan masukkan OTP, QR, token, secret, atau file sesi.", file=stream)
    bot = input_fn("Nomor bot (format internasional +...): ").strip()
    if not validator.bot_number_valid(bot):
        print(BOT_FORMAT_ERROR, file=stream)
        bot = ""
        return 2
    owner = input_fn("ID owner kanonik (...@s.whatsapp.net): ").strip()
    if not owner_id_valid(owner):
        print(OWNER_FORMAT_ERROR, file=stream)
        bot = owner = ""
        return 2
    try:
        manifest = build_manifest(bot, owner)
        yaml_text = dump_yaml(manifest)
        report = validator.audit_text(yaml_text)
        if output_path.exists() or output_path.is_symlink():
            print("TERBLOKIR: pilot.local.yaml sudah ada; tidak ditimpa.", file=stream)
            return 2
        output_path.write_text(yaml_text, encoding="utf-8")
    except OSError:
        print("TERBLOKIR: manifest lokal tidak dapat dibuat.", file=stream)
        return 2
    finally:
        bot = owner = ""

    print_reduced_status(report, stream=stream)
    if (
        any(report[key] is None for key in validator.FIELDS)
        or report["runtime_isolation_status"] != "LULUS"
        or report["send_enabled"] is not False
    ):
        print("TERBLOKIR: gateway dan pairing tetap dilarang.", file=stream)
        return 2
    print("VALIDATOR_LULUS; gateway tetap menunggu persetujuan owner berikutnya.", file=stream)
    return 0


def cli(argv=None):
    parser = argparse.ArgumentParser(description="Buat manifest pilot lokal; tidak menjalankan gateway.")
    parser.add_argument("--one-group", action="store_true", help="minta satu ID grup @g.us melalui prompt lokal tanpa echo")
    parser.add_argument("--two-groups", action="store_true", help="minta tepat dua ID grup @g.us melalui prompt lokal tanpa echo")
    args = parser.parse_args(argv)
    if args.one_group and args.two_groups:
        parser.error("pilih hanya satu dari --one-group atau --two-groups")
    if args.one_group:
        return main_one_group()
    return main_two_groups() if args.two_groups else main()


if __name__ == "__main__":
    raise SystemExit(cli())
