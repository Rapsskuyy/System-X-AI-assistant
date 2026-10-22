"""Tambahkan hingga lima grup allowlist lewat prompt lokal tanpa echo."""
import argparse
import getpass
import subprocess
from pathlib import Path
from ruamel.yaml import YAML

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "pilot.one-group.v2.local.yaml"
TARGET = HERE / "pilot.multigroup.v3.local.yaml"


def valid_group(value):
    return isinstance(value, str) and value.endswith("@g.us") and value[:-5].isdigit() and 8 <= len(value[:-5]) <= 24


def main(argv=None):
    parser = argparse.ArgumentParser(description="Tambahkan ID grup baru lewat prompt lokal tanpa echo.")
    parser.parse_args(argv)
    if TARGET.exists() or TARGET.is_symlink():
        print("TERBLOKIR: manifest multi-grup sudah ada; tidak ditimpa.")
        return 2
    yaml = YAML(typ="safe", pure=True)
    data = yaml.load(SOURCE.read_text(encoding="utf-8"))
    pilot = data.get("x_wa_pilot_audit") if isinstance(data, dict) else None
    if not isinstance(pilot, dict) or not isinstance(pilot.get("allowlisted_groups"), list):
        print("TERBLOKIR: manifest sumber tidak valid.")
        return 2
    raw = getpass.getpass("ID grup baru @g.us, pisahkan koma (tanpa echo): ").strip()
    supplied = [item.strip() for item in raw.split(",") if item.strip()]
    raw = ""
    if not supplied or not all(valid_group(item) for item in supplied):
        print("TERBLOKIR: masukkan ID grup @g.us yang valid; tidak ada perubahan.")
        return 2
    groups = list(dict.fromkeys([*pilot["allowlisted_groups"], *supplied]))
    supplied = []
    if len(groups) > 5:
        print("TERBLOKIR: maksimal lima grup allowlist; tidak ada perubahan.")
        return 2
    pilot["allowlisted_groups"] = groups
    yaml_out = YAML()
    yaml_out.default_flow_style = False
    with TARGET.open("w", encoding="utf-8") as handle:
        yaml_out.dump(data, handle)
    group_csv = ",".join(groups)
    subprocess.run(["hermes", "config", "set", "X_GROUP_SUMMARY_POLICY_PATH", str(TARGET).replace("\\", "/")], check=True)
    subprocess.run(["hermes", "config", "set", "WHATSAPP_GROUP_ALLOWED_USERS", group_csv], check=True)
    print(f"SELESAI: total_grup={len(groups)}; duplikat_diabaikan; restart gateway untuk menerapkan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
