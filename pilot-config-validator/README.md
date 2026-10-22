# Validator konfigurasi pilot (lokal, read-only)

Hanya membaca YAML lokal lewat `ruamel.yaml` yang sudah tersedia pada interpreter Hermes saat dibuat. Tidak mengimpor adapter, mengakses `.env`, membaca sesi, membuka jaringan, atau menulis konfigurasi. Tidak memasang paket. Tidak untuk menyalakan pilot.

Jalankan dari folder ini:

```text
python -B -m unittest discover -s tests -v
python -B setup_pilot.py
python -B setup_pilot.py --one-group
python -B setup_pilot.py --two-groups
python -B validator.py --config data/dummy_config.yaml
python -B validator.py
```

`setup_pilot.py` meminta nomor bot dan ID owner melalui prompt lokal tanpa echo. Ia membuat `pilot.local.yaml` di folder ini dengan kebijakan DM-owner-only tetap: `group_policy: disabled`, `allowlisted_groups: []`, `sender_policy: owner_only`, dan pengirim lain `reject`; outbound/media/lampiran/URL/tool grup/log teks mentah nonaktif, default deny, kill switch aktif, dan TTL 60 detik. Berkas tersebut diabaikan oleh `.gitignore`, tidak menyentuh konfigurasi Hermes, dan tidak pernah ditimpa otomatis. Jalankan langsung di terminal lokal; jangan kirim nilainya melalui chat. Setelah membuat berkas, skrip menampilkan hanya sembilan status tereduksi dan berhenti TERBLOKIR karena isolasi runtime belum lulus.

`setup_pilot.py --one-group` membaca hanya identitas bot/owner yang sudah ada dari `pilot.local.yaml`, lalu meminta **satu** ID grup lewat prompt lokal tanpa echo. Ia membuat `pilot.one-group.local.yaml` yang tidak ditimpa otomatis dan diabaikan Git. Manifest ini menetapkan allowlist satu grup, observasi semua teks grup tanpa mention, buffer metadata/ringkasan sementara selama 24 jam (tanpa menyimpan teks mentah), tanpa balasan otomatis di grup, dan pengiriman rangkuman hanya ke DM owner atas permintaan owner. Tool/terminal grup, media/lampiran, URL preview, dan logging teks mentah tetap nonaktif. Gateway ditandai nonaktif dan tidak pernah dijalankan oleh skrip; output hanya status tereduksi tanpa ID atau isi pesan.

`setup_pilot.py --two-groups` memakai kontrol yang sama untuk tepat dua grup dan membuat `pilot.two-group.local.yaml`.

Perintah terakhir hanya membaca kandidat `$HERMES_HOME/config.yaml`; jika `HERMES_HOME` tidak ada, gagal tertutup. Keluaran hanya status kebijakan tereduksi, tanpa ID atau payload. Exit code `2` berarti TERBLOKIR/tidak siap, bahkan pada dummy yang terbaca; exit code bukan izin untuk gateway. Jangan memasukkan `--config` yang menunjuk ke file rahasia.

Skema `x_wa_pilot_audit` pada `data/dummy_config.yaml` adalah **kontrak contoh buatan proyek**, bukan pengaturan WhatsApp yang dikenali Hermes. Jangan menyalinnya ke konfigurasi Hermes. Pada konfigurasi Hermes yang tidak memiliki blok tersebut, `config_readable=true` hanya berarti YAML dapat dibaca; semua kontrol pilot tetap `null` (BELUM DIUJI). `runtime_isolation_status` selalu `BELUM_DIUJI` karena file konfigurasi tidak dapat membuktikan ACL/identitas proses. Nilai `kill_switch_configured` hanya menilai field dummy, bukan sakelar efektif. Validator tidak membaca override dari `.env` atau mengklaim status adapter efektif. Format YAML yang rusak, file hilang, symlink, ukuran >1 MiB, atau parser tidak tersedia menghasilkan `config_readable=false` dan semua kontrol pilot `null`.

Contoh audit data dummy (ID dalam berkas input tidak pernah ditampilkan):

```json
{"config_readable":true,"pilot_enabled":true,"send_enabled":false,"group_count":0,"owner_configured":true,"media_enabled":false,"url_preview_enabled":false,"kill_switch_configured":true,"runtime_isolation_status":"BELUM_DIUJI"}
```

Contoh ini bukan bukti mode kirim atau allowlist pilot sebenarnya. Pilot tetap TERBLOKIR sampai sumber konfigurasi efektif, override, dan isolasi runtime diverifikasi secara terpisah dengan persetujuan owner. Tidak ada gateway, pairing, QR, atau koneksi jaringan.
