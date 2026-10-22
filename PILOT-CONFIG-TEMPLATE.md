# Template konfigurasi audit pilot X — dummy saja

Dokumen ini menjelaskan **kontrak contoh** yang benar-benar dibaca `pilot-config-validator/validator.py`. Blok `x_wa_pilot_audit` **bukan** pengaturan yang dikenali adapter WhatsApp Hermes. Jangan menyalin template ini ke `config.yaml` Hermes, jangan mengisinya dengan ID/nomor nyata di repositori, dan jangan menganggap hasilnya izin mengaktifkan pilot. Tidak ada gateway, pairing, atau koneksi dalam template ini.

## Placeholder sintetis — bukan nilai nyata

Contoh berikut hanya untuk berkas dummy lokal terpisah. Teks dalam tanda `<...>` adalah placeholder, **bukan** ID akun yang terverifikasi.

```yaml
x_wa_pilot_audit:
  enabled: false
  send_enabled: false
  group_policy: disabled
  allowlisted_groups: []
  owner_id: "<ID_OWNER_DUMMY>@s.whatsapp.net"
  sender_policy: owner_only
  unauthorized_sender_behavior: reject
  media_enabled: false
  attachments_enabled: false
  url_preview_enabled: false
  kill_switch_configured: true
  kill_switch_active: true
  ttl_seconds: 60
  group_tool_execution_enabled: false
  raw_message_logging_enabled: false
  default_deny: true
```

Mode ini menonaktifkan grup (`group_policy: disabled`) dan mewajibkan daftar grup kosong. Hanya satu owner berakhiran `@s.whatsapp.net` yang boleh berinteraksi; pengirim lain wajib `reject`. Untuk audit dummy, semua field pada contoh perlu diisi eksplisit; jangan mengandalkan default tersirat. `enabled: false` dan `send_enabled: false` dipertahankan selama belum ada persetujuan owner terpisah. Nilai nyata tidak boleh ditaruh di dokumen ini maupun dimasukkan ke fixture proyek. Validator hanya memeriksa bentuk ID dan policy dummy; ia **tidak** membuktikan identitas kanonik, kepemilikan, atau keabsahan ID.

## Field input yang dibaca validator

| Field di `x_wa_pilot_audit` | Isian dummy yang diwajibkan | Penilaian validator (output) |
|---|---|---|
| `enabled` | `false` | Boolean eksplisit → `pilot_enabled` sama nilainya; hilang/bukan boolean → `null`. Tidak membuktikan adapter Hermes aktif/nonaktif. |
| `send_enabled` | `false` | Boolean eksplisit → `send_enabled` sama nilainya; hilang/bukan boolean → `null`. Tidak membuktikan kemampuan outbound nyata nonaktif. |
| `group_policy` dan `allowlisted_groups` | `disabled` dan `[]` | `group_policy` harus tepat `disabled`; daftar kosong menghasilkan `group_count: 0`. Setiap grup atau kebijakan grup lain membatalkan status pilot dummy. |
| `owner_id` | Satu placeholder owner berakhiran `@s.whatsapp.net` | String dengan prefiks non-kosong dan akhiran tersebut → `owner_configured: true`; string tak sesuai → `false`; hilang/bukan string → `null`. Hanya bentuk, bukan autentikasi owner. |
| `sender_policy` dan `unauthorized_sender_behavior` | `owner_only` dan `reject` | Keduanya wajib persis demikian agar kontrak dummy menganggap hanya owner boleh berinteraksi dan pengirim lain ditolak. |
| `media_enabled` **dan** `attachments_enabled` | Keduanya `false` | Jika salah satu `true` → `media_enabled: true`; keduanya eksplisit `false` → `false`; selain itu → `null`. Lampiran tidak punya field output terpisah. |
| `url_preview_enabled` | `false` | Boolean eksplisit → `url_preview_enabled` sama nilainya; hilang/bukan boolean → `null`. |
| `kill_switch_configured` | `true` | Boolean eksplisit → `kill_switch_configured` sama nilainya; hilang/bukan boolean → `null`. `true` **bukan** bukti sakelar lokal aktif, terbaca saat runtime, atau fail-closed. |

Nilai `null` berarti BELUM DIUJI, **bukan** `false`. Nilai `true` pada `send_enabled`, `media_enabled`, atau `url_preview_enabled` bertentangan dengan batas pilot ini. Jumlah grup selain nol atau kebijakan grup selain `disabled` juga bertentangan dengan mode DM-owner-only. Jika blok `x_wa_pilot_audit` tidak ada, seluruh kontrol pilot bernilai `null` sekalipun berkas YAML dapat dibaca.

## Output tambahan yang bukan field input

- `config_readable`: `true` hanya jika berkas lokal dapat dibaca sebagai mapping YAML dengan parser aman yang tersedia. Berkas hilang, symlink, lebih dari 1 MiB, format tidak valid, atau parser tak tersedia → `false`. Ini **tidak** berarti konfigurasi WhatsApp efektif terbukti.
- `runtime_isolation_status`: selalu `BELUM_DIUJI`; validator tidak membaca field input untuk itu. Status tersebut memerlukan bukti proses, hak filesystem efektif, dan kebijakan jaringan di staging terpisah. Jangan menambahkan `runtime_isolation_status: LULUS` ke YAML untuk mengubah keluaran.

## TTL buffer dan retensi — belum dinilai validator

`SyntheticTTLBuffer` pada `simulator.py` memakai TTL **60 detik** dalam simulasi dan buffer dibersihkan setelah pemrosesan. Validator **tidak membaca** `ttl_seconds`, kebijakan retensi, atau lokasi penyimpanan; menambah field semacam itu ke blok dummy tidak akan memverifikasi TTL. Penghapusan buffer dan tidak adanya log teks mentah harus diuji secara terpisah; jangan mengklaim retensi pilot nyata aman dari keluaran validator.

## Batas penggunaan

Validator hanya mengeluarkan sembilan status tereduksi, tidak pernah mengeluarkan ID, isi pesan, atau nilai lain dari YAML. Ia tidak membaca `.env`/override, tidak memeriksa status adapter efektif, tidak memverifikasi kill switch runtime, dan selalu mengembalikan exit code `2` (TERBLOKIR). Placeholder dummy dan nilai nyata sengaja dipisahkan: nilai nyata hanya boleh ditangani nanti lewat prosedur persetujuan owner dan verifikasi independen; tidak ada nilai nyata disediakan atau diminta di sini.
